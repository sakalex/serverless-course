import datetime
import decimal
import json
import traceback
import typing as t
import uuid
import re

import boto3

from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda

_LOG = get_logger('ApiHandler-handler')
PREFIX = "cmtr-62505701-"
SUFFIX="-test"
USER_POOL_NAME = f"{PREFIX}simple-booking-userpool{SUFFIX}"
USER_POOL_CLIENT_NAME = "simple-booking-client"
cognito_client = boto3.client("cognito-idp")
tables_table = boto3.resource("dynamodb").Table(f"{PREFIX}Tables{SUFFIX}")
reservations_table = boto3.resource("dynamodb").Table(f"{PREFIX}Reservations{SUFFIX}")

class ApiHandler(AbstractLambda):

    def validate_request(self, event: dict) -> t.Optional[dict]:
        pass

    def handle_request(self, event: dict, context: dict) -> dict:

        _LOG.info(f"Event: {event}")
        try:
            method = event["requestContext"]["httpMethod"]
            path:str = event["requestContext"]["path"]

            if path.startswith("/api"):
                path = path.replace("/api", "")

            request_body = {}

            if "body" in event and event["body"]:
                request_body = json.loads(event["body"])

            _LOG.info(f"Method: {method}, Path: {path}, Request body: {request_body}")

            if method == "POST" and path == "/signup":
                email = request_body["email"]
                first_name = request_body["firstName"]
                last_name = request_body["lastName"]
                password = request_body["password"]

                self.signup(email, first_name, last_name, password)

                return {"statusCode": 200}
            elif method == "POST" and path == "/signin":
                email = request_body["email"]
                password = request_body["password"]

                access_token = self.signin(email, password)

                return {
                    "statusCode": 200,
                    "body": json.dumps({"accessToken": access_token})
                }
            elif method == "GET" and path == "/tables":
                # self.authorize_user(event)

                tables = self.get_tables()
                _LOG.info(f"Tables: {tables}")

                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "tables": tables
                    })
                }
            elif method == "POST" and path == "/tables":
                # self.authorize_user(event)
                id = int(request_body["id"])
                number = int(request_body["number"])
                places = int(request_body["places"])
                is_vip = bool(request_body["isVip"])
                min_order = None
                if "minOrder" in request_body:
                    min_order = int(request_body["minOrder"])

                table_id = self.create_table(id, number, places, is_vip, min_order)

                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "id": table_id
                    })
                }
            elif method == "GET" and re.match(r"^/tables/\d+$", path):
                # self.authorize_user(event)
                table_id = int(path.split("/")[-1])

                table = self.get_table(table_id)
                _LOG.info(f"Table: {table}")

                return {
                    "statusCode": 200,
                    "body": json.dumps(table)
                }
            elif method == "POST" and path == "/reservations":
                # self.authorize_user(event)
                table_number = int(request_body["tableNumber"])
                client_name = request_body["clientName"]
                phone_number = request_body["phoneNumber"]
                date = request_body["date"]
                slot_time_start = request_body["slotTimeStart"]
                slot_time_end = request_body["slotTimeEnd"]

                reservation = self.create_reservation(
                    table_number, 
                    client_name, 
                    phone_number, 
                    date, 
                    slot_time_start, 
                    slot_time_end
                )
                _LOG.info(f"Reservation: {reservation}")

                return {
                    "statusCode": 200,
                    "body": json.dumps({"reservationId": reservation})
                }
            elif method == "GET" and path == "/reservations":
                # self.authorize_user(event)

                reservations = self.get_reservations()
                _LOG.info(f"Reservations: {reservations}")

                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "reservations": reservations
                    })
                }
            else:
                _LOG.error(f"Path not found: {path}")
                return {
                    "statusCode": 404,
                    "body": "Not Found"
                }
        except Exception as e:
            _LOG.error(f"Failed to handle request: {e}\n{traceback.format_exc()}")
            _LOG.error(f"Event: {event}, Context: {context}")
            return {"statusCode": 400}

    def get_user_pool_id(self, user_pool_name: str) -> str:

        user_pool_id = None
        response = cognito_client.list_user_pools(MaxResults=50)
        _LOG.info(f"User pools: {response}")

        user_pool_id = None
        for user_pool in response["UserPools"]:
            if user_pool["Name"] == user_pool_name:
                user_pool_id = user_pool["Id"]
                break

        if user_pool_id is None:
            raise ValueError(f"User pool {USER_POOL_NAME} not found")

        return user_pool_id

    def get_user_pool_client_id(self, user_pool_id: str) -> str:

        client_id = None
        response = cognito_client.list_user_pool_clients(
            UserPoolId=user_pool_id,
            MaxResults=50
        )
        _LOG.info(f"User pool clients: {response}")

        for client in response["UserPoolClients"]:
            if client["ClientName"] == USER_POOL_CLIENT_NAME:
                client_id = client["ClientId"]
                break

        if client_id is None:
            raise ValueError(f"User pool client not found")

        return client_id

    def serialize(self, data: t.Any) -> t.Any:

        if isinstance(data, list):
            return [self.serialize(item) for item in data]
        elif isinstance(data, dict):
            return {key: self.serialize(value) for key, value in data.items()}
        elif isinstance(data, decimal.Decimal):
            return int(data)

        return data

    def validate_email(self, email: str) -> None:
        
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
            raise ValueError("Invalid email")

    def validate_password(self, password: str) -> None:
        
        if not re.match(r"^(?=.*[a-zA-Z])(?=.*\d)(?=.*[^\w\s]).{12,}$", password):
            raise ValueError("Invalid password")
    
    def signup(self, email: str, first_name: str, last_name: str, password: str) -> None:
        _LOG.info(f"Signing up user: {email}")

        self.validate_email(email)
        self.validate_password(password)

        user_pool_id = self.get_user_pool_id(USER_POOL_NAME)

        response = cognito_client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=email,
            UserAttributes=[
                {
                    "Name": "given_name",
                    "Value": first_name 
                },
                {
                    "Name": "family_name",
                    "Value": last_name 
                },
                {
                    "Name": "email",
                    "Value": email 
                }
            ],
            TemporaryPassword=password,
            MessageAction="SUPPRESS",
        )
        _LOG.info(f"create user response: {response}")

        response = cognito_client.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=email,
            Password=password,
            Permanent=True,
        )
        _LOG.info(f"set user password response: {response}")

    def signin(self, email: str, password: str) -> str:
        _LOG.info(f"Signing in user: {email}")

        self.validate_email(email)
        self.validate_password(password)

        user_pool_id = self.get_user_pool_id(USER_POOL_NAME)
        client_id = self.get_user_pool_client_id(user_pool_id)

        response = cognito_client.initiate_auth(
            ClientId=client_id,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": email,
                "PASSWORD": password
            }
        )
        access_token = response["AuthenticationResult"]["IdToken"]
        return access_token

    def get_tables(self) -> list[dict]:
        _LOG.info("Getting tables")
        response = tables_table.scan()
        tables = response["Items"]
        tables = self.serialize(tables)
        tables = sorted(tables, key=lambda table: table["id"])
        return tables

        
    def is_overlapping(
        self,
        start1: str,
        end1: str, 
        start2: str,
        end2: str,
    ) -> bool:

        start1 = datetime.datetime.strptime(start1, "%H:%M").time()
        end1= datetime.datetime.strptime(end1, "%H:%M").time()
        start2 = datetime.datetime.strptime(start2, "%H:%M").time()
        end2 = datetime.datetime.strptime(end2, "%H:%M").time()

        if start1 <= start2 <= end1 or start1 <= end2 <= end1:
            return True

        return False


    def create_table(
        self, 
        id: int, 
        number: int, 
        places: int,
        is_vip: bool,
        min_order: t.Optional[int] = None,
    ) -> int:
        _LOG.info(f"Creating table: {id}")
        item = {
            "id": id,
            "number": number,
            "places": places,
            "isVip": is_vip,
        } 
        if min_order is not None:
            item["minOrder"] = min_order
        tables_table.put_item(Item=item)
        return id 
    
    def get_table(self, table_id: int) -> dict:
        _LOG.info(f"Getting table: {table_id}")
        response = tables_table.get_item(Key={"id": table_id})
        table = response["Item"]
        table = self.serialize(table)
        return table

    def create_reservation(
        self, 
        table_number: int, 
        client_name: str,
        phone_number: str,
        date: str,
        slot_time_start: str,
        slot_time_end: str,
    ) -> str:
        _LOG.info(f"Creating reservation for table: {table_number}")
        response = tables_table.scan() 
        tables = response["Items"]
        for table in tables:
            if table["number"] == table_number:
                break
        else:
            raise ValueError(f"Table {table_number} not found")

        reservations = self.get_reservations()
        for reservation in reservations:
            if reservation["tableNumber"] == table_number and reservation["date"] == date:
                reservation_start = reservation["slotTimeStart"]
                reservation_end = reservation["slotTimeEnd"]
                if self.is_overlapping(reservation_start, reservation_end, slot_time_start, slot_time_end):
                    raise ValueError("Reservation time is overlapping with another reservation")

        reservation_id = str(uuid.uuid4())
        item = {
            "id": reservation_id,
            "tableNumber": table_number,
            "clientName": client_name,
            "phoneNumber": phone_number,
            "date": date,
            "slotTimeStart": slot_time_start,
            "slotTimeEnd": slot_time_end,
        }
        reservations_table.put_item(Item=item)
        return reservation_id

    def get_reservations(self) -> list[dict]:
        _LOG.info("Getting reservations")
        response = reservations_table.scan()
        reservations = response["Items"]
        reservations = self.serialize(reservations)
        return reservations

HANDLER = ApiHandler()


def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)
