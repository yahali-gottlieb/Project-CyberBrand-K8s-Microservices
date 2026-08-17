import json
import os
import copy
import uuid
import logging
import subprocess

class Machine:
    def __init__(self, name: str, os_type: str, cpu: int, ram: int):
        self.name = name
        self.os_type = os_type
        self.cpu = cpu
        self.ram = ram
        self.instance_id = f"i-{uuid.uuid4().hex[:16]}"
        self.instance_type = self._determine_instance_type()
        
        logging.info(f"[PYTHON] Machine object created: {self.name} [{self.instance_type}]")

    def _determine_instance_type(self) -> str:
        aws_types = [
            (1, 1, "t2.micro"),
            (1, 2, "t2.small"),
            (2, 4, "t2.medium"),
            (2, 8, "t2.large"),
            (4, 8, "c5.xlarge"),
            (4, 16, "t2.xlarge"),
            (8, 32, "t2.2xlarge"),
            (16, 64, "m5.4xlarge"),
            (32, 128, "m5.8xlarge")
        ]
        
        for c, r, instance_type in aws_types:
            if self.cpu <= c and self.ram <= r:
                return instance_type
                
        return "m5.8xlarge"

    def to_dict(self, template_instance: dict) -> dict:
        new_instance = copy.deepcopy(template_instance)
        
        new_instance["InstanceId"] = self.instance_id
        new_instance["KeyName"] = self.name
        new_instance["CpuOptions"]["CoreCount"] = self.cpu
        new_instance["InstanceType"] = self.instance_type
        
        for tag in new_instance.get("Tags", []):
            if tag["Key"] == "Name":
                tag["Value"] = self.name
                
        return new_instance

    def save_to_json(self, filepath: str):
        if not os.path.exists(filepath):
            logging.error(f"[PYTHON] Cannot find {filepath} to clone from.")
            return

        try:
            with open(filepath, 'r') as f:
                aws_data = json.load(f)
                
            instances_list = aws_data["Reservations"][0]["Instances"]
            template_instance = instances_list[0]
            
            formatted_dict = self.to_dict(template_instance)
            instances_list.append(formatted_dict)
            
            with open(filepath, 'w') as f:
                json.dump(aws_data, f, indent=4)
                
            logging.info(f"[PYTHON] Successfully saved {self.name} to {filepath}")
            
        except Exception as e:
            logging.error(f"[PYTHON] Failed to save machine to JSON: {e}")

    def provision_service(self, script_path: str):
        if not os.path.exists(script_path):
            logging.error(f"[PYTHON] Provisioning skipped: Script '{script_path}' not found.")
            return

        logging.info(f"[PYTHON] Triggering Bash provisioning script for {self.name}...")
        
        try:
            subprocess.run(["bash", script_path], check=True)
            logging.info(f"[PYTHON] Provisioning script completed successfully for {self.name}.")
            
        except subprocess.CalledProcessError as e:
            logging.error(f"[PYTHON] Provisioning script failed with exit code {e.returncode}.")
            
        except Exception as e:
            logging.error(f"[PYTHON] An unexpected error occurred during provisioning: {e}")