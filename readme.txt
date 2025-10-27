How to Run:

1. Open the project folder in your terminal or command prompt.

2. Create a virtual environment:
	python -m venv env

3. Activate the virtual environment:
   On Windows:
	env\Scripts\activate
   On macOS/Linux:
	source env/bin/activate

4. Install the required packages:
	pip install -r requirements.txt

5. Run the Flask application file (eg. in VSCode or terminal), "SDM CV Connect.py" 

6. Open your web browser and go to:
	http://127.0.0.1:5000

7. To stop the server, press Ctrl + C in the terminal.

-----------------------------------------------------------------

Notes:
- Python 3.10 or later is required.
- The database file (test.db) is created automatically when the app is first run.
- If the models are updated or you want to clear the database, delete test.db and rerun the app to recreate the database.