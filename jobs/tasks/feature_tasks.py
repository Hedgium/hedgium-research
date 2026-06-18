from celery import shared_task

from analysis.ml.predict import predict_universe
from features.services.compute import compute_features_universe


@shared_task(name="jobs.tasks.feature_tasks.compute_features_daily")
def compute_features_daily():
    result = compute_features_universe()
    predict_result = predict_universe()
    return {"features": result, "predictions": predict_result}
