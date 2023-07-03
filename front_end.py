from modules.hsparkapi import API
from POC.db import DB
from POC.poc import POC
from shiny import App, reactive, render, ui
from pathlib import Path
from datetime import datetime
import json




# Get all query_* endpoints except query_vehicle_trips (which is a special case)
# Remove the "query_" prefix from each method name.  This will be the name of the endpoint.
endpoints: list = ["_".join(method.split("_")[1:]) for method in dir(API) if method.startswith("query_") and method != "query_vehicle_trips"]

# Defines the UI layout for the app
app_ui = ui.page_fluid(
    # Login modal
    ui.modal(
        (
            # ui.input_text(id="username", label="HARMAN Spark Username", placeholder="username"),
            ui.input_password(id="username", label="HARMAN Spark Username"),
            ui.input_password(id="password", label="HARMAN Spark Password"),
            ui.output_text("auth_status")
        ),
        title = "HARMAN Spark Authentication",
        easy_close = False, # Prevents the user from closing the modal by clicking outside of it
        footer=(
            ui.input_action_button("authenticate", "Submit Credentials", class_="btn-primary")
        )
    ),

    # Header & Logo
    ui.img(src="logo.png", width="100px"),
    ui.h1(
        ui.output_text("header_text")
    ),

    # Main UI
    ui.input_selectize(id="endpoint", label="Endpoint", choices=endpoints),
    ui.output_ui(id="vehicle_id_display"), # Conditional: Shows default vehicle ID only if the endpoint uses it
    ui.output_ui(id="vehicle_id_select"), # Conditional: Shows vehicle ID selection only of the switch to update it is toggled
    ui.input_radio_buttons(id="data_options", label="Data Options", choices=["Current Data", "Historical Data", "Current and Historical Data"]),
    ui.output_ui(id="record_cnt_display"), # Conditional: Shows record count only if the query should return historical data
    ui.input_action_button(id="query_submit", label="Submit", class_="btn-primary"),
    ui.output_table(id="results_table"),

    # Custom message handler to hide the modal since shiny.ui.modal_remove() doesn't work
    ui.tags.script(
        """
        $(function() {
            Shiny.addCustomMessageHandler("hide_modal", function(message) {
                $('#shiny-modal').modal('hide');
                console.log(message);
            });
        });
        """
    )
)


def server(input, output, session):
    """
    Defines the server logic for the app including reactive values and event handlers
    """
    db: DB = DB()
    poc: POC = POC()
    api: API = reactive.Value()
    authed: bool = reactive.Value(False)
    access_token: str = reactive.Value("")
    expires_at: str = reactive.Value("")
    modal_str: str = reactive.Value("")
    hashed_user: int = reactive.Value(0)
    default_vehicle_id: str = reactive.Value(None)

    # Basic I/O
    @output
    @render.text
    def header_text():
        return "Spark + Py"
    
    @output
    @render.text
    def default_vehicle_id_text():
        return f"Default Vehicle ID: {default_vehicle_id.get()}" if default_vehicle_id.get() is not None else ""

    @output
    @render.ui
    @reactive.event(input.endpoint)
    def vehicle_id_display():
        if input.endpoint().startswith("vehicle_"):
            return (
                ui.output_text("default_vehicle_id_text"),
                ui.input_switch("select_different_vehicle", "Update Default Vehicle ID?", value=False),
            )
        
    @output
    @render.text
    def auth_status():
        return modal_str.get()
        
   
    # Conditional UI Elements
    @output
    @render.ui
    @reactive.event(input.select_different_vehicle)
    def vehicle_id_select():
        """
        Shows the vehicle ID selection input only if the user toggles the switch to update the default vehicle ID
        """
        if input.select_different_vehicle():
            return ui.input_select(
                id="new_default_vehicle_id", 
                label="Select Default Vehicle ID",
                # Using a dict of dict for choices because it allows Shiny to implement the <optgroup> tag, not possible with a dict of list
                # This is just a quality of life thing for the user
                # https://shiny.rstudio.com/py/api/ui.input_select.html
                choices={
                    "Default": {default_vehicle_id.get(): default_vehicle_id.get()}, 
                    "All Associated": {vehId:vehId for vehId in api.get().all_associated_vehicles()}
                },
                selected=default_vehicle_id.get()
            )
        else:
            return ui.output_text("def_vehicle_id")
    
    @output
    @render.ui
    @reactive.event(input.data_options)
    def record_cnt_display():
        """
        Shows the record count input only if the user selects "Historical Data" or "Current and Historical Data"
        """
        if "Historical" in input.data_options():
            return ui.input_numeric(id="record_cnt", label="Total Number of Entries to Display", value=3)    
        

    # Event Handlers
    @reactive.Effect
    @reactive.event(authed)
    async def _hide_modal():
        """ 
        Called whenever the "authed" reactive value changes
        If the user is authenticated, it uses a custom handler to close the authentication modal
        """
        if authed.get():
            await session.send_custom_message("hide_modal", "Hiding modal!")

    @reactive.Effect
    @reactive.event(input.new_default_vehicle_id)
    def _update_vehicle_id():
        """
        Called whenever a new default vehicle ID is selected from the dropdown
        Updates the default vehicle ID in the database if the user changes it from the current value
        """
        if input.new_default_vehicle_id() is not None and input.new_default_vehicle_id() != default_vehicle_id.get():
            db.insert_update_vehicle_id(hashed_user.get(), default_vehicle_id.get())
            default_vehicle_id.set(input.new_default_vehicle_id())


    # Main Logic (Authentication and Querying)
    @output
    @render.table
    @reactive.event(input.query_submit)
    def results_table():
        """
        Handles querying the API and DB and returning the results to the UI
        """

        # If the Data Option is "Current Data" or "Current and Historical Data", we need to query the API
        if input.data_options().startswith("Current"):

            # Get all query_* methods from the api object
            # Can't just pull from dir(API) because it will return the method from the class, not the object
            query_methods = {endpoint: getattr(api.get(), f"query_{endpoint}") for endpoint in endpoints}
            
            # Grab method and determine if it uses the vehicleId parameter
            method = query_methods[input.endpoint()]
            uses_vehId: bool = "vehicleId" in method.__code__.co_varnames
            resp = method(default_vehicle_id.get()) if uses_vehId else method()
            
            # Insert response into DB
            db.insert_response_record(
                user_hash = hashed_user.get(), 
                retrieve_dt_tm = datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z"),
                endpoint = input.endpoint(),
                response_data = json.dumps(resp),
                vehicle_id = default_vehicle_id.get() if uses_vehId else None
            )

        # Query the DB for the response, only pulling the most recent record if the user selected "Current Data"
        return db.get_endpoint_response(
            user_hash=hashed_user.get(),
            endpoint=input.endpoint(),
            record_cnt=input.record_cnt() if "Historical" in input.data_options() else 1,
            vehicle_id=default_vehicle_id.get() if str(input.endpoint()).startswith("vehicle_") else None,
        )
    

    @reactive.Effect
    @reactive.event(input.authenticate)
    def authenticate():
        """
        Handles authentication with the API
        """
        try:
            # Check for valid token in DB first, request new token if not found
            credentials = poc.attempt_auth_flow(input.username(), input.password())
        except Exception as e:
            # If there's an error, display it to the user and don't set the credentials
            # This will cause the modal to stay open but the program won't fully close so the user can refresh and try again
            modal_str.set(f"Error trying to authenticate: {str(e)}")
            ui.notification_show(
                (
                    ui.h1("Error!"), 
                    ui.h3(str(e)),
                    ui.p("Please refresh the page and try again.")
                ),
                type="error"
            )
        if credentials is not None:
            # Set reactive values and instantiate the API object
            access_token.set(credentials["access_token"])
            expires_at.set(credentials["expires_at"])
            api_local = API(access_token.get())
            api.set(api_local)
            hashed_user.set(poc.constant_hash(input.username()))
            default_vehicle_id.set(db.get_default_vehicle_id(hashed_user.get()))
            modal_str.set("Success!")
            authed.set(True) # This will trigger the _hide_modal() reactive effect
            ui.notification_show(
                (
                    ui.h1("Success!"), 
                    ui.p("You have successfully authenticated against the HARMAN Spark API.")
                ),
                type="message",
                close_button=True,
                duration=None
            )
        else:
            # If the credentials are invalid, display an error to the user
            modal_str.set("Error!")
            ui.notification_show(
                (
                    ui.h1("Error!"), 
                    ui.p("Could not validate against Harman Spark API with the provided credentials.")
                ),
                type="error"
            )

dir = Path(__file__).parent
app = App(app_ui, server, static_assets=dir, debug=True)