"""Train the forecasting models and save them to backend/models.

Run from the backend folder:  python -m scripts.train_model
"""
import time

from app.infrastructure.config.settings import settings
from app.infrastructure.ml.panel import panel_from_frame, read_transactions
from app.infrastructure.ml.training import held_out_users, save_models, train


def main():
    started = time.time()
    panel = panel_from_frame(read_transactions(settings.data_dir), settings.start_date, settings.end_date)
    print(f"{len(panel.users)} users in the data, {len(held_out_users(panel))} kept out of training")
    models = train(panel, settings)
    path = save_models(models, settings.model_dir)
    first, last = models["trained_on"]["first_origin"], models["trained_on"]["last_origin"]
    print(f"forecasts made from {first} to {last}; nothing after {settings.train_end} was used")
    print(f"saved {path.name} ({path.stat().st_size / 1e6:.1f} MB) in {time.time() - started:.0f}s")


if __name__ == "__main__":
    main()
