from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from pathlib import Path
from csv import reader

main = Blueprint('main', __name__)
parent_dir = Path(__file__).parent.parent
guide_files = parent_dir / 'templates' / 'components' / 'guide'


def load_csv_files_in_directory():
	csv_data = {}
	for file in guide_files.iterdir():
		if file.suffix == '.csv':
			with open(file, "r", newline="") as csv_file:
				guide_reader = reader(csv_file, delimiter=';')
				data = []
				for row in guide_reader:
					row_set = list(row)
					data.append(row_set)
				csv_data[file.stem] = data
	return csv_data


@main.route('/')
def index():
	if current_user.is_authenticated:
		guide_tag = request.args.get('guide')
		guide = load_csv_files_in_directory()
	else:
		guide = None
		guide_tag = None
	return render_template('index.html', guide=guide, guide_tag=guide_tag)


@main.route('/profile')
@login_required
def profile():
	return render_template('profile.html', name=current_user.name)


@main.route('/goof')
@login_required
def goof():
	return render_template('goof.html')
