import asyncio
import sys
from sqlalchemy.exc import IntegrityError
from core.browser import MizukiBrowser
from parsers.extractor import extract_price_heuristic
from database.connection import SessionLocal
from database.models import TargetURL, ScrapingResult

# --- funções de gerenciamento (síncronas) ---

def add_urls_interface():
    """loop para adicionar URLs ao banco via terminal"""
    db = SessionLocal()
    print("\n--- Adição de URLS ---")
    print("Cole a URL e dê Enter. Digite 'sair' para voltar ao menu.")
    
    while True:
        url = input("URL >> ").strip()
        if url.lower() in ['sair', 'exit', 'q']:
            break
        
        if not url.startswith('http'):
            print("❌ URL inválida (deve começar com http/https)")
            continue

        try:
            target = TargetURL(url=url)
            db.add(target)
            db.commit()
            print(f"✅ Salvo no banco: {url}")
        except IntegrityError:
            db.rollback()
            print("⚠️  URL já existe no banco de dados.")
        except Exception as e:
            db.rollback()
            print(f"❌ Erro ao salvar: {e}")
    
    db.close()

def list_targets():
    """lista o que temos no banco para processar"""
    db = SessionLocal()
    targets = db.query(TargetURL).filter(TargetURL.active == True).all()
    print(f"\n--- fila de processamento ({len(targets)} URLs) ---")
    for t in targets:
        print(f"[{t.id}] {t.url}")
    print("----------------------------------")
    db.close()
    return targets

# --- funções da Mizuki (Assíncronas) ---

async def worker(target_obj, browser_instance, semaphore):
    """processa uma URL específica vinda do banco"""
    async with semaphore:
        result = await browser_instance.get_page_content(target_obj.url)
        
        price = None
        if result['status'] == 'success':
            price = extract_price_heuristic(result['html'])
            print(f"💰 Preço detectado: {price} | em {target_obj.url[:40]}...")
        
        # salvando resultado vinculado ao Alvo
        db = SessionLocal()
        try:
            # cria o log do resultado
            record = ScrapingResult(
                target_id=target_obj.id,
                status=result['status'],
                html_snapshot=result['html'] if result['status'] == 'success' else None,
                price_found=price
            )
            db.add(record)
            db.commit()
        except Exception as e:
            print(f"Erro ao salvar resultado: {e}")
        finally:
            db.close()

async def run_bot():
    """pega URLs do banco e inicia o scraping"""
    targets = list_targets()
    if not targets:
        print("Nenhuma URL para processar. Adicione algumas primeiro!")
        return

    print("\n🚀 Iniciando Mizuki Scraper...")
    browser_tool = MizukiBrowser()
    semaphore = asyncio.Semaphore(3) # Máximo de 3 abas simultâneas
    
    tasks = [worker(t, browser_tool, semaphore) for t in targets]
    
    await asyncio.gather(*tasks)
    print("\n🏁 Processamento finalizado com sucesso!")

# --- MENU PRINCIPAL ---

def main_menu():
    while True:
        print("\n=== MIZUKI BOT ===")
        print("1. Adicionar urls")
        print("2. Ver fila de processamento")
        print("3. Iniciar Mizuki")
        print("0. Sair")
        
        choice = input("Escolha uma opção: ")
        
        if choice == '1':
            add_urls_interface()
        elif choice == '2':
            list_targets()
        elif choice == '3':
            asyncio.run(run_bot())
        elif choice == '0':
            print("Sayonara! 👋")
            sys.exit()
        else:
            print("Opção inválida.")

if __name__ == "__main__":
    main_menu()