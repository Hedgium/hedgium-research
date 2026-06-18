from celery import shared_task

from analysis.ml.predict import predict_universe
from analysis.ml.train import train_all_models


@shared_task(name="jobs.tasks.ml_tasks.train_prediction_model_weekly")
def train_prediction_model_weekly():
    return train_all_models()


@shared_task(name="jobs.tasks.ml_tasks.predict_universe_daily")
def predict_universe_daily():
    return predict_universe(use_ensemble=True)
