# Author: Natalia Tylek (12332258), Marlene Riegel (01620782), Maximilian Kleinegger (12041500)
# Created: 2025-01-13

set -e

ENV_NAME=".amp-skiplist"

python -m venv $ENV_NAME

source $ENV_NAME/bin/activate

pip install --upgrade pip
pip install -r ./requirements.txt
pip install ipykernel
python -m ipykernel install --user --name=$ENV_NAME --display-name "Python ($ENV_NAME)"

echo "Setup complete. To activate the virtual environment, run 'source $ENV_NAME/bin/activate'"