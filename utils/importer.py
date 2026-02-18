import os
from sqlalchemy.orm import Session
from database.connection import SessionLocal
from database.models import Product, Pharmacy, Category, Region
from core.normalization import clean_url, identify_pharmacy, classify_product

def import_from_txt(file_path="targets.txt"):
    """
    Lê um arquivo .txt padronizado e popula o novo schema.
    Formato esperado: URL; PRECO_ALVO; CODIGO_REGIAO
    """
    if not os.path.exists(file_path):
        print(f"❌ Arquivo {file_path} não encontrado.")
        return

    db: Session = SessionLocal()
    count = 0

    print("🔄 Iniciando importação e normalização...")

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'): continue

            try:
                # 1. Parse da linha
                parts = line.split(';')
                raw_url = parts[0].strip()
                target_price = float(parts[1].strip()) if len(parts) > 1 and parts[1].strip() else None
                region_code = parts[2].strip() if len(parts) > 2 else "BR-GEN"

                # 2. Normalização (Ponto 2)
                final_url = clean_url(raw_url)
                
                # 3. Gestão de Farmácia (Ponto 1)
                pharm_name, pharm_domain = identify_pharmacy(final_url)
                pharmacy = db.query(Pharmacy).filter_by(domain=pharm_domain).first()
                if not pharmacy:
                    pharmacy = Pharmacy(name=pharm_name, domain=pharm_domain)
                    db.add(pharmacy)
                    db.commit()

                # 4. Gestão de Categoria (Ponto 3 - Placeholder, será atualizado após o scraping pegar o nome real)
                # Por enquanto, classificamos como "Pendente"
                category = db.query(Category).filter_by(name="Pendente").first()
                if not category:
                    category = Category(name="Pendente", classification_logic="*")
                    db.add(category)
                    db.commit()

                # 5. Gestão de Região (Ponto 5)
                region = db.query(Region).filter_by(region_code=region_code).first()
                if not region:
                    region = Region(name=f"Região {region_code}", region_code=region_code)
                    db.add(region)
                    db.commit()

                # 6. Upsert do Produto
                product = db.query(Product).filter_by(url=final_url).first()
                if not product:
                    product = Product(
                        url=final_url,
                        canonical_url=final_url,
                        product_name="Aguardando Scan...", # Será atualizado pelo scraper
                        pharmacy_id=pharmacy.id,
                        category_id=category.id,
                        target_price=target_price,
                        active=True
                    )
                    db.add(product)
                    print(f"✅ Novo produto adicionado: {pharm_name}")
                    count += 1
                else:
                    # Atualiza meta de preço se mudou
                    if target_price: 
                        product.target_price = target_price
                    print(f"ℹ️ Produto já existe, atualizado: {pharm_name}")

            except Exception as e:
                print(f"❌ Erro na linha: {line}. Erro: {e}")

    db.commit()
    db.close()
    print(f"🏁 Importação concluída. {count} novos produtos.")

if __name__ == "__main__":
    # Cria categorias padrão se não existirem
    db = SessionLocal()
    defaults = ["Estrogen", "Antiandrogen", "Testosterone", "Blocker", "Outros", "Pendente"]
    for cat in defaults:
        if not db.query(Category).filter_by(name=cat).first():
            db.add(Category(name=cat, classification_logic="auto"))
    db.commit()
    db.close()
    
    import_from_txt()