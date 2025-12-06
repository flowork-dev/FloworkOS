########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\websocket_server_service\websocket_server_service.py total lines 195 
########################################################################

import asyncio
import websockets
import logging
import time
import msgpack
from web3 import Web3
from eth_account.messages import encode_defunct
from eth_account import Account
import re
from flowork_kernel.router import StrategyRouter


ETH_ADDRESS_REGEX = re.compile(r'^0x[a-fA-F0-9]{40}$')
class WebSocketServerService:
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self.logger = logging.getLogger(self.__class__.__name__)
        self.server = None
        self.gateway_connector = None
        self.db_service = None
        self.job_queue = None
        self.router = None
        self.logger.info("WebSocketServerService initialized (Standalone Mode).")
        self._initialized = True
    def setup(self, host, port, gateway_connector, db_service, job_queue):
        self.host = host
        self.port = port
        self.gateway_connector = gateway_connector
        self.db_service = db_service
        self.job_queue = job_queue
        self.router = StrategyRouter(["default","fast","thorough"])
        self.logger.info(f"Setup complete. Ready to serve on {host}:{port}")
    def is_valid_ethereum_address(self, address: str) -> bool:
        if not isinstance(address, str):
            return False
        if not ETH_ADDRESS_REGEX.match(address):
            return False
        try:
            return Web3.is_address(address)
        except Exception:
            return ETH_ADDRESS_REGEX.match(address) is not None
    def verify_web3_signature(self, address: str, message: str, signature: str) -> bool:
        if not all([address, message, signature]):
            self.logger.warning("[Auth] Signature verification failed: Missing address, message, or signature.")
            return False
        if not self.is_valid_ethereum_address(address):
            self.logger.warning(f"[Auth] Signature verification failed: Invalid Ethereum address format: {address}")
            return False
        try:
            message_hash = encode_defunct(text=message)
            signer_address = Account.recover_message(message_hash, signature=signature)
            if signer_address.lower() == address.lower():
                self.logger.debug(f"[Auth] Signature verified successfully for address: {address}")
                return True
            else:
                self.logger.warning(f"[Auth] Signature verification failed: Mismatched address. Expected {address}, got {signer_address}")
                return False
        except Exception as e:
            self.logger.error(f"[Auth] Signature verification error for address {address}: {e}", exc_info=True)
            return False
    def authenticate(self, auth_data):

        try:
            address = auth_data.get('address')
            signature = auth_data.get('signature')
            timestamp = auth_data.get('timestamp')
            message = auth_data.get('message')
            if not all([address, signature, timestamp, message]):
                return False, "Missing auth data (address, signature, timestamp, message)"
            try:
                if abs(int(timestamp) - int(time.time())) > 60:
                    self.logger.warning(f"Auth failed: Timestamp expired for {address}")
                    return False, "Timestamp expired"
            except ValueError:
                 return False, "Invalid timestamp format"
            whitelist = self.gateway_connector.get_whitelisted_addresses()
            normalized_whitelist = [str(addr).lower() for addr in whitelist]
            if str(address).lower() not in normalized_whitelist:
                self.logger.warning(f"Auth failed: Address {address} not in whitelist.")
                return False, "User not authorized"
            if not self.verify_web3_signature(address, message, signature):
                self.logger.warning(f"Auth failed: Invalid signature for address {address}")
                return False, "Invalid signature"
            self.logger.info(f"Auth successful: User {address} authenticated.")
            return True, address
        except Exception as e:
            self.logger.error(f"Error during authentication: {e}", exc_info=True)
            return False, "Internal auth error"


    async def handle_message(self, websocket, user_address, message_data):

        action = message_data.get('action')


        self.logger.debug(f"Handling action '{action}' for user {user_address}")

        if action == 'run_workflow':

            workflow_id = message_data.get('workflow_id')
            session_id = message_data.get('session_id')

            if not session_id:
                 self.logger.warning(f"'run_workflow' from {user_address} missing 'session_id'.")
                 response = {"status": "error", "message": "session_id is required for run_workflow"}
                 await websocket.send(msgpack.dumps(response, use_bin_type=True))
                 return


            if workflow_id:
                self.logger.info(f"User {user_address} requested to run workflow {workflow_id} (Session: {session_id})")

                context = {"force_strategy": message_data.get("strategy")} if message_data.get("strategy") else {}
                strategy = self.router.pick(context)
                self.logger.info(f"(R5) Strategy selected for workflow {workflow_id}: {strategy}")

                try:

                    self.job_queue.put({
                        "type": "workflow_start",
                        "workflow_id": workflow_id,
                        "user_address": user_address,
                        "strategy": strategy,
                        "session_id": session_id,
                    })
                    response = {"status": "success", "message": f"Workflow {workflow_id} started."}
                except Exception as e:
                    self.logger.error(f"Failed to put job in queue: {e}", exc_info=True)
                    response = {"status": "error", "message": "Failed to queue job."}
                await websocket.send(msgpack.dumps(response, use_bin_type=True))
            else:
                response = {"status": "error", "message": "workflow_id missing"}
                await websocket.send(msgpack.dumps(response, use_bin_type=True))

    async def handler(self, websocket, path):
        self.logger.info(f"New connection attempt from {websocket.remote_address}")
        user_address = None
        try:
            auth_message_bytes = await websocket.recv()
            auth_data = msgpack.loads(auth_message_bytes, raw=False)
            if auth_data.get('action') != 'auth':
                await websocket.close(1002, "Auth message required")
                return
            is_authenticated, auth_detail = self.authenticate(auth_data.get('payload'))
            if not is_authenticated:
                self.logger.warning(f"Auth failed for {websocket.remote_address}: {auth_detail}")
                await websocket.close(1008, auth_detail)
                return
            user_address = auth_detail
            auth_success_msg = {"status": "success", "message": "Authentication successful"}
            await websocket.send(msgpack.dumps(auth_success_msg, use_bin_type=True))

            async for message_bytes in websocket:
                try:
                    message_data = msgpack.loads(message_bytes, raw=False)


                    await self.handle_message(websocket, user_address, message_data)

                except msgpack.exceptions.UnpackException as e:
                    self.logger.error(f"Failed to decode msgpack message: {e}")
                    error_msg = {"status": "error", "message": "Invalid message format (must be msgpack)"}
                    await websocket.send(msgpack.dumps(error_msg, use_bin_type=True))
                except Exception as e:
                    self.logger.error(f"Error handling message: {e}", exc_info=True)
                    error_msg = {"status": "error", "message": "Internal server error"}
                    await websocket.send(msgpack.dumps(error_msg, use_bin_type=True))
        except websockets.exceptions.ConnectionClosed as e:
            self.logger.info(f"Connection closed for user {user_address}: {e.code} {e.reason}")
        except Exception as e:
            self.logger.error(f"Unhandled WebSocket error for user {user_address}: {e}", exc_info=True)
            if websocket.open:
                await websocket.close(1011, "Server error")
        finally:
            pass

    async def start(self):
        if not self.gateway_connector or not self.db_service or not self.job_queue:
            self.logger.critical("Services not set up. Call setup() first.")
            return
        self.logger.info(f"Starting WebSocket server on {self.host}:{self.port}...")
        self.server = await websockets.serve(self.handler, self.host, self.port)
        await self.server.wait_closed()
    async def stop(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.logger.info("WebSocket server stopped.")
