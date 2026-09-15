from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def home():
    # 1. Initialize an empty list to store the parsed items
    parsed_alerts = []

    # 2. Open and read our local log file line by line
    with open("firewall.log", "r") as file:
        for line in file:
            # Clean up hidden line breaks and split by the commas
            line = line.strip()
            if not line:
                continue  # Skip any blank lines

            parts = line.split(",")

            # 3. Structural Logic: Turn the text row into a clean dictionary
            alert_dict = {
                "ip": parts[0],
                "status": parts[1],
                "message": parts[2]
            }

            # 4. Add our newly formatted dictionary to our data pile
            parsed_alerts.append(alert_dict)

    # 5. Send our dynamically extracted data straight to the web browser
    return render_template("dashboard.html", alerts=parsed_alerts)


if __name__ == "__main__":
    app.run(debug=True)
