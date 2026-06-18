from django.core.management.base import BaseCommand

from analysis.ml.train import train_all_models, train_prediction_model
from analysis.ml.trainers import ALL_MODEL_TYPES, DEFAULT_VERSIONS


class Command(BaseCommand):
    help = "Train 30-day direction classifiers (xgboost, lightgbm, catboost)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--model-type",
            default="all",
            choices=["all", *ALL_MODEL_TYPES],
            help="Train one model or all three",
        )
        parser.add_argument("--model-version", default=None, dest="model_version")
        parser.add_argument("--index", default="NIFTY50")
        parser.add_argument("--sample-step", type=int, default=5)
        parser.add_argument("--test-size", type=float, default=0.2)

    def handle(self, *args, **options):
        model_type = options["model_type"]

        if model_type == "all":
            result = train_all_models(
                index_name=options["index"],
                sample_step=options["sample_step"],
                test_size=options["test_size"],
            )
        else:
            version = options["model_version"] or DEFAULT_VERSIONS[model_type]
            result = train_prediction_model(
                model_type=model_type,
                version=version,
                index_name=options["index"],
                sample_step=options["sample_step"],
                test_size=options["test_size"],
            )

        style = self.style.SUCCESS if result.get("status") in ("success", "partial") else self.style.ERROR
        self.stdout.write(style(str(result)))
