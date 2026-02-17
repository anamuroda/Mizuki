import pandas as pd
from prophet import Prophet
from database.connection import SessionLocal
from database.models import ScrapingResult

def forecast_price(target_id):
    """(Pilar 3) IA de Previsão"""
    db = SessionLocal()
    history = db.query(ScrapingResult).filter(
        ScrapingResult.target_id == target_id,
        ScrapingResult.price > 0
    ).order_by(ScrapingResult.scraped_at).all()
    db.close()

    if len(history) < 10: return "Dados insuficientes para IA."

    df = pd.DataFrame([{'ds': h.scraped_at, 'y': h.price} for h in history])
    
    try:
        m = Prophet(daily_seasonality=True)
        m.fit(df)
        future = m.make_future_dataframe(periods=5)
        forecast = m.predict(future)
        pred = forecast.tail(1)['yhat'].values[0]
        return f"Previsão (5 dias): R$ {pred:.2f}"
    except:
        return "Erro na previsão."