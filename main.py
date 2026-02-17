import asyncio
import sys
import os
from sqlalchemy.exc import IntegrityError
from core.browser import MizukiBrowser
from parsers.extractor import extract_hybrid 
from database.connection import SessionLocal
from database.models import TargetURL, ScrapingResult
from core.scheduler import start_scheduler
from core.logger import logger

# --- FUNÇÕES DE GERENCIAMENTO (Síncronas) ---

def add_target_interface():
    """Interface de Terminal para adicionar URLs"""
    print("\n--- ADICIONAR NOVO ALVO ---")
    url = input("🔗 Cole a URL do produto: ").strip()
    if not url: return
    
    prod_name = input("🏷️  Nome do Produto (opcional): ").strip() or "Produto Sem Nome"
    
    try:
        price_target = float(input("🎯 Qual seu preço alvo (ex: 100.00)? Digite 0 para ignorar: ") or 0)
    except:
        price_target = 0.0
        
    db = SessionLocal()
    try:
        target = TargetURL(url=url, product_name=prod_name, target_price=price_target)
        db.add(target)
        db.commit()
        print(f"✅ Sucesso! {prod_name} adicionado ao monitoramento.")
    except IntegrityError:
        db.rollback()
        print("⚠️  URL já existe no banco de dados.")
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao salvar: {e}")
    finally:
        db.close()

async def run_manual_scan():
    """Roda uma verificação manual AGORA (sem esperar o agendador)"""
    print("\n🚀 Iniciando varredura manual...")
    db = SessionLocal()
    targets = db.query(TargetURL).filter(TargetURL.active == True).all()
    db.close()

    if not targets:
        print("Nenhum alvo cadastrado.")
        return

    browser = MizukiBrowser()
    
    for target in targets:
        print(f"🔎 Verificando: {target.product_name}...")
        try:
            result = await browser.fetch_page(target.url)
            
            # CORREÇÃO: Usando a nova função híbrida
            price, available, method = extract_hybrid(result['html'])
            
            print(f"   ↳ Preço: R$ {price:.2f} | Disp: {available} | Método: {method}")
            
            # Salva resultado
            db = SessionLocal()
            res = ScrapingResult(
                target_id=target.id,
                price=price,
                available=available,
                method=method
            )
            db.add(res)
            db.commit()
            db.close()

        except Exception as e:
            print(f"   ↳ ❌ Falha: {e}")

# --- MENU PRINCIPAL ---

async def main():
    print("=== 🎌 MIZUKI INTELLIGENCE (MODO LOCAL) 🎌 ===")
    
    while True:
        print("\n1. Adicionar URL para monitorar")
        print("2. Rodar Verificação AGORA (Manual)")
        print("3. Iniciar Agendador (Automático - 10:00 AM)")
        print("0. Sair")
        
        opt = input(">> ")
        
        if opt == '1':
            add_target_interface()
        elif opt == '2':
            await run_manual_scan()
        elif opt == '3':
            print("⏳ Iniciando Agendador... (O bot rodará todo dia às 10h)")
            print("   Pressione Ctrl+C para parar.")
            scheduler = start_scheduler()
            
            # Mantém o script rodando infinitamente para o agendador funcionar
            while True:
                await asyncio.sleep(1)
        elif opt == '0':
            print("Sayonara! 👋")
            sys.exit()
        else:
            print("Opção inválida.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass