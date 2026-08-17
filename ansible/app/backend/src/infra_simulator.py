import argparse
import os
import logging
import subprocess
from pydantic import BaseModel, Field, ValidationError
from ansible.app.src.machine import Machine

os.makedirs('logs', exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S', filename='logs/provisioning.log', filemode='a')

class InstanceConfig(BaseModel):
    name: str = Field(..., min_length=2)
    os: str = Field(..., min_length=2)
    cpu: int = Field(..., gt=0, le=32) 
    ram: int = Field(..., gt=0, le=128)

def main():
    parser = argparse.ArgumentParser(description="Deploy an EC2 instance by typing the required parameters."
    "For example: --name myvm --os Ubuntu --cpu 4 --ram 8. For provisioning only, use --provision without any other parameters.")
    
    parser.add_argument("--name", help="Name of the machine")
    parser.add_argument("--os", help="Operating System (e.g., Ubuntu, Windows, etc.)")
    parser.add_argument("--cpu", help="Number of CPU cores")
    parser.add_argument("--ram", help="Amount of RAM in GB")
    parser.add_argument("--provision", action="store_true", help="Run the Bash provisioning script")
    
    filepath = os.path.join("configs", "instances.json")
    script_path = os.path.join("scripts", "install_service.sh")
    args = parser.parse_args()

    if args.provision and not any([args.name, args.os, args.cpu, args.ram]):
        print("Running standalone provisioning script...")
        logging.info("[PYTHON] Running standalone provisioning via CLI flag.")
        try:
            subprocess.run(["bash", script_path], check=True)
            print("Provisioning complete!")
        except Exception as e:
            print("Provisioning failed. Check logs/provisioning.log.")
            logging.error(f"[PYTHON] Standalone provisioning failed: {e}")
        return

    if any([args.name, args.os, args.cpu, args.ram]) and not all([args.name, args.os, args.cpu, args.ram]):
        print("Error: To create a new machine, you must provide --name, --os, --cpu, AND --ram.")
        return

    if all([args.name, args.os, args.cpu, args.ram]):
        try:
            config = InstanceConfig(name=args.name, os=args.os, cpu=args.cpu, ram=args.ram)
            
            new_vm = Machine(
                name=config.name, 
                os_type=config.os, 
                cpu=config.cpu, 
                ram=config.ram
            )
            
            new_vm.save_to_json(filepath)
            print(f"Machine '{config.name}' deployed successfully to JSON!")
            
            if args.provision:
                print(f"Running provisioning script for {config.name}...")
                new_vm.provision_service(script_path)
                print("Provisioning complete! Check logs/provisioning.log for detailed output.")
            
        except ValidationError as e:
            logging.error(f"[PYTHON] User Input Validation Error for machine '{args.name}'")
            print("Validation Error! Check your inputs:")
            
            for err in e.errors():
                loc = err.get('loc', [''])[0]
                msg = err.get('msg', '')
                bad_input = getattr(args, str(loc), 'Unknown')
                error_details = f"Argument '--{loc}': {msg} (Input provided: '{bad_input}')"
                
                logging.error(f"  - {error_details}")
                print(f"  - {error_details}")
    
    elif not args.provision:
        parser.print_help()

if __name__ == "__main__":
    main()