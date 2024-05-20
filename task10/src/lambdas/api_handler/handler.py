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
cognito_client = boto3.client("cognito-idp")
tables_table = boto3.resource("dynamodb").Table(f"{PREFIX}Tables{SUFFIX}")
reservations_table = boto3.resource("dynamodb").Table(f"{PREFIX}Reservations{SUFFIX}")


class ApiHandler(AbstractLambda):

    def validate_request(self, event: dict) -> t.Optional[dict]:
        pass

    def handle_request(self, event: dict, context: dict) -> dict:

        _LOG.info(f"Event: {event}")
        try:
            method = event["requestContext"]["http"]["method"]
            path = event["rawPath"]
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
                    "body": json.dumps(reservation)
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
            _LOG.error(f"Failed to handle request: {e}, {traceback.format_exc()}")
            return {"statusCode": 400}

    def validate_access_token(self, access_token: str) -> None:
        cognito_client.get_user(AccessToken=access_token)    

    def get_access_token(self, event: dict) -> str:
        return event["headers"]["Authorization"].split(" ")[1]

    def authorize_user(self, event: dict) -> None:
        access_token = self.get_access_token(event)
        self.validate_access_token(access_token)

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

        client_id = response["UserPoolClients"][0]["ClientId"]

        if client_id is None:
            raise ValueError(f"User pool client not found")

        return client_id
    
    def signup(self, email: str, first_name: str, last_name: str, password: str) -> None:
        _LOG.info(f"Signing up user: {email}")

        user_pool_id = self.get_user_pool_id(USER_POOL_NAME)

        cognito_client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=email,
            UserAttributes=[
                {
                    "Name": "email",
                    "Value": email 
                }
            ],
            TemporaryPassword=password,
            MessageAction="SUPPRESS",
        )

    def signin(self, email: str, password: str) -> str:
        _LOG.info(f"Signing in user: {email}")

        user_pool_id = self.get_user_pool_id(USER_POOL_NAME)
        client_id = self.get_user_pool_client_id(user_pool_id)

        response = cognito_client.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            AuthFlow="ADMIN_USER_PASSWORD_AUTH",
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
        return tables

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
        return reservations

HANDLER = ApiHandler()


def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)
