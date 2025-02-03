from flask import Flask, request, jsonify, send_file
from app.render import ScheduleRenderer
from core.schedule import Schedule
from core.roster import Roster
from core.stats import AssignmentStats
from core.history import AssignmentHistory
from util import assignments_from_html
from logging.config import dictConfig
from logging import info
import json
import os
import pdfkit

from util.helpers import write_dict_to_file


# TODO move scheduling classes into /app/schedule/services/..
# include here as blueprint
# run.py goes away
def create_app(
    schedule: Schedule,
    roster: Roster,
    history: AssignmentHistory,
    stats: AssignmentStats,
    **options,
) -> Flask:

    initialize_logger()

    app = Flask("Congregation Roster", static_folder="app/static")
    app.config.from_mapping(options["options"])
    app.app_context

    # TODO blueprints
    # TODO Move to views
    renderer = ScheduleRenderer(schedule, roster, stats)

    @app.put("/commit")
    def commit():
        """
        Commit schedule to persistent storage (rn, previous-assignments.json)

        The last commit json is stored in a tmp working file so we can undo
        and apply new changes
        """

        if os.path.exists(app.config["TMP_WORKING_PATH"]):
            with open(app.config["TMP_WORKING_PATH"], "r") as f:
                assignments = json.loads(f.read())

                if assignments != schedule.assignments:
                    history.remove_assignments(assignments)
                else:
                    return jsonify({"message": "success"}), 304

        # update json
        history.record_assignments(schedule.assignments)

        # write new assignments to tmp working dir
        write_dict_to_file(schedule.assignments, app.config["TMP_WORKING_PATH"])

        return jsonify({"message": "success"}), 200

    @app.get("/pdf")
    def download_pdf():
        pdf_output_filename = f"schedule-{schedule.month}-{schedule.year}.pdf"
        html = renderer.render_schedule_to_html(interactive=False)

        with open(app.config["HTML_OUTPUT_PATH"], "w+") as f:
            f.write(html)

        pdfkit.from_file(
            app.config["HTML_OUTPUT_PATH"],
            app.config["PDF_OUTPUT_PATH"],
            options={
                "orientation": "Landscape",
                "page-size": "Legal",
                "enable-local-file-access": "",
            },
        )

        return send_file(
            app.config["PDF_OUTPUT_PATH"],
            mimetype="application/pdf",
            download_name=pdf_output_filename,
            as_attachment=True,
        )

    @app.post("/save")
    def save():
        """
        update schedule with new changes

        write json assignments to json output so we don't lose work if
        server crashes, run script will read from there
        TODO instead of sending the entire html page, send json schedule format
        """
        new_schedule_html = request.data.decode("utf-8")
        new_assignments = assignments_from_html(new_schedule_html)

        # set new assignments
        schedule.set_assignments(new_assignments)

        # json output
        write_dict_to_file(schedule.assignments, app.config["JSON_OUTPUT_PATH"])

        return jsonify({"message": "success"}), 204

    @app.get("/")
    def get_schedule():
        # TODO cache using hash of assignment dict to key?
        schedule_html = renderer.render_schedule_to_html()

        return schedule_html

    return app


def initialize_logger():
    dictConfig(
        {
            "version": 1,
            "formatters": {
                "default": {
                    "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
                }
            },
            "handlers": {
                "wsgi": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                    "formatter": "default",
                }
            },
            "root": {"level": "INFO", "handlers": ["wsgi"]},
        }
    )
