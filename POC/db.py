from sqlalchemy import create_engine, text, TextClause
from sqlalchemy.engine import Connection, Engine
from typing import Optional, Union
import pandas as pd

class DB:
    engine: Engine
    conn: Connection = None
    user: str = "spark"
    password: str = "HS9YkPj50Hqzol7IEsIb"
    host: str = "192.168.1.54"
    port: str = "5432"
    db_name: str = "spark"
    conn_string = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db_name}"

    def __init__(self):
        """
        Initializes the database connection
        Connection details are hardcoded since this class only exists for 1 project
        """
        self.engine = create_engine(self.conn_string)

    def __del__(self):
        """
        Destructor that closes the connection to the database if it is still open and disposes of the engine
        """
        if self.conn:
            self.conn.close()
        if self.engine:
            self.engine.dispose()

    def connect(self) -> None:
        """
        Connects to the database if the connection is not already open
        """
        if not self.conn or not self.conn._still_open_and_dbapi_connection_is_valid:
            self.conn = self.engine.connect()

    def disconnect(self) -> None:
        """
        Disconnects from the database if the connection is still open
        """
        if self.conn._still_open_and_dbapi_connection_is_valid:
            self.conn.close()

    def execute(self, sql: str, commit: bool = False, parameters: Optional[dict] = None):
        """
        Executes a query against the database directly using sqlalchemy
        Useful for DDL statements
        :param sql: SQL query to be executed. Params are represented by :param_name
        :param commit: Whether or not to commit the transaction after executing the query
        :param parameters: Parameters to be passed to the query
        """
        self.connect()
        result = self.conn.execute(text(sql), parameters=parameters)
        if commit:
            self.conn.commit()
        return result
    
    def df_query(self, sql: str, params: Optional[dict] = None) -> pd.DataFrame:
        """
        Executes a query using pandas and returns the results as a pandas dataframe
        :param sql: SQL query to be executed. Params are represented by %(param_name)s
        :param params: Parameters to be passed to the query
        :return: Pandas dataframe of query results
        """
        self.connect()
        df = pd.read_sql_query(sql, self.conn, params=params)
        return df

    def insert_update_auth_data(self, user_hash: int, pass_hash: int, user_token: str, user_token_expire_dt_tm: str) -> None:
        """
        Inserts or updates (if user_hash already present) the pass/token/expiry in the auth_data table
        :param user_hash: Hashed username
        :param pass_hash: Hashed password
        :param user_token: User token
        :param user_token_expire_dt_tm: User token expiry datetime
        """
        sql = text(f"""
        INSERT INTO spark.public.auth_data (user_hash, pass_hash, user_token, user_token_expire_dt_tm)
        VALUES ({user_hash}, {pass_hash}, '{user_token}', '{user_token_expire_dt_tm}')
        ON CONFLICT (user_hash)
        DO UPDATE SET
            pass_hash = excluded.pass_hash, user_token = excluded.user_token, user_token_expire_dt_tm = excluded.user_token_expire_dt_tm;
        """)
        print(user_hash)
        print(pass_hash)
        print(user_token)
        print(user_token_expire_dt_tm)
        self.conn.execute(sql)
        self.conn.commit()


    def username_exists(self, hashed_username: int) -> bool:
        """
        Checks if the username exists in the database
        :param hashed_username: Hashed username
        :return: Boolean representing presence of username in database
        """
        sql: str = f"SELECT EXISTS(SELECT 1 FROM public.auth_data WHERE user_hash = {hashed_username})"
        result = self.execute(sql)
        return result.fetchone()[0]

    def password_matches(self, hashed_username: int, hashed_password: int) -> bool:
        """
        Checks if the password matches the username in the database
        :param hashed_username: Hashed username
        :param hashed_password: Hashed password
        :return: Boolean representing password match with given username
        """
        sql: str = f"SELECT EXISTS(SELECT 1 FROM public.auth_data WHERE user_hash = {hashed_username} AND pass_hash = {hashed_password})"
        result = self.execute(sql)
        return result.fetchone()[0]

    def get_user_token_details(self, hashed_username: int) -> dict:
        """
        Gets the user token and expiration date from the database
        :param hashed_username: Hashed username
        :return: Dictionary containing user token and expiration date
        """
        sql: str = f"SELECT user_token, user_token_expire_dt_tm FROM public.auth_data WHERE user_hash = {hashed_username}"
        result = self.df_query(sql)
        return result.to_dict(orient="records")[0]
    
    # TODO: Add type for retrieve_dt, maybe Union datetime/str with the pd type
    # Should response be dict or str?
    def insert_response_record(self, user_hash: int, retrieve_dt_tm: str, endpoint: str, response_data: str, vehicle_id: Optional[str] = None) -> None:
        """
        Inserts a record into the response_data table
        :param user_hash: Hashed username
        :param retrieve_dt_tm: Datetime of retrieval
        :param endpoint: Endpoint that was retrieved
        :param response_data: Response data from endpoint
        :param vehicle_id: Vehicle ID (if applicable)
        """
        sql = r"""INSERT INTO spark.public.response_data (user_hash, retrieve_dt_tm, endpoint, response_data, vehicle_id)
        VALUES(:user_hash, :retrieve_dt_tm, :endpoint, :response_data, NULLIF(:vehicle_id, 'None'))"""
        params = {"user_hash": user_hash, "retrieve_dt_tm": retrieve_dt_tm, "endpoint": endpoint, "response_data": response_data, "vehicle_id": vehicle_id}
        self.execute(sql, commit=True, parameters=params)


    def get_endpoint_response(self, user_hash: int, endpoint: str, record_cnt: int, vehicle_id: Optional[str] = None) -> pd.DataFrame:
        """
        Get the response data for a given endpoint for a given user (and vehicle for vehicle endpoints)
        :param user_hash: Hashed username
        :param endpoint: Endpoint to retrieve data for
        :param record_cnt: Number of records to retrieve
        :param vehicle_id: Vehicle ID to retrieve data for (if applicable)
        :return: Pandas DataFrame containing response data

        Note:
        Returns a wide DataFrame with the response_data expanded into columns and the retrieve_dt_tm as a column
        """
        sql = r"""SELECT 
            response_data,
            retrieve_dt_tm 
        FROM spark.public.response_data
        WHERE 
            user_hash = %(user_hash)s 
            AND endpoint = %(endpoint)s 
            AND COALESCE(vehicle_id, 'None') = %(vehicle_id)s
        ORDER BY retrieve_dt_tm DESC
        LIMIT %(record_cnt)s"""
        vehicle_id = vehicle_id if vehicle_id else "None"
        params = {"user_hash": user_hash, "endpoint": endpoint, "record_cnt": record_cnt, "vehicle_id": vehicle_id}
        result = self.df_query(sql, params=params)
        # Use to_list on response_data to try to expand json into columns
        # Merge the retrieve_dt_tm with the wide response_data
        return pd.merge(pd.DataFrame(result["response_data"].tolist()), pd.DataFrame(result["retrieve_dt_tm"]), left_index=True, right_index=True)
    
    def get_default_vehicle_id(self, user_hash: int) -> str:
        """
        Gets the default vehicle_id for the user from user_preferences table
        :param user_hash: Hashed username
        """
        sql = r"""SELECT default_vehicle_id FROM spark.public.user_preferences WHERE user_hash = %(user_hash)s"""
        params = {"user_hash": user_hash}
        result = self.df_query(sql, params=params)
        try:
            result = result["default_vehicle_id"].to_list()[0]
        except IndexError:
            result = None
        return result
    
    def insert_update_vehicle_id(self, user_hash: int, vehicle_id: str) -> None:
        """
        Inserts or updates (if user_hash already present) the user_preferences table with the provided values
        :param user_hash: Hashed username
        :param vehicle_id: Vehicle ID
        """
        sql = text(f"""
        INSERT INTO spark.public.user_preferences (user_hash, default_vehicle_id)
        VALUES ({user_hash}, '{vehicle_id}')
        ON CONFLICT (user_hash)
        DO UPDATE SET
            default_vehicle_id = excluded.default_vehicle_id;
        """)
        self.conn.execute(sql)
        self.conn.commit()
        