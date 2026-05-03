#!/usr/bin/env python3
"""
Script to fetch filter efficiencies from CMS MCM (Monte Carlo Management)

For MiniAOD datasets, this script will attempt to:
1. Find the chained request from the dataset
2. Fetch all requests in the chain (requires authentication)
3. Locate the wmLHEGEN/wmLHEGS request containing filter efficiency

LIMITATIONS without authentication:
- Cannot fetch chain information (public API does not provide chain data)
- The "Chain" field with actual PrepIDs is only available via authenticated API
- PrepID inference from chain name may match wrong physics process
- Not all requests are accessible via public API

For reliable results, use one of these methods:
1. Use MCM web interface to find correct wmLHEGEN PrepID
2. Use authenticated access with valid CERN SSO cookie
3. Search for the wmLHEGEN dataset directly if known

Usage:
    ./fetchMCMFilterEfficiency.py --prepid <PrepID>
    ./fetchMCMFilterEfficiency.py --dataset <dataset_name>
    ./fetchMCMFilterEfficiency.py --chain <chain_PrepID>
    
Authentication:
    Create CERN SSO cookie using:
    auth-get-sso-cookie -u https://cms-pdmv.cern.ch/mcm -o ~/.cern-sso-cookie.txt
"""

import argparse
import json
import requests
import sys
import os
from typing import Dict, List, Optional, Union


class MCMInterface:
    """Interface to interact with CMS MCM API"""
    
    def __init__(self, dev: bool = False):
        """
        Initialize MCM interface
        
        Args:
            dev: If True, use development MCM instance
        """
        self.base_url = "https://cms-pdmv-dev.cern.ch/mcm" if dev else "https://cms-pdmv.cern.ch/mcm"
        self.session = requests.Session()
        self._setup_authentication()
    
    def _setup_authentication(self):
        """Setup authentication using CERN SSO cookie"""
        # Check for common locations of CERN SSO cookies
        cookie_locations = [
            os.path.expanduser("~/.cern-sso-cookie.txt"),
            os.path.expanduser("~/private/prod-cookie.txt"),
            os.path.expanduser("~/private/dev-cookie.txt"),
        ]
        
        for cookie_file in cookie_locations:
            if os.path.exists(cookie_file):
                try:
                    with open(cookie_file, 'r') as f:
                        cookie_content = f.read().strip()
                        # auth-get-sso-cookie creates a file with format:
                        # domain\tFALSE\tpath\tFALSE\texpiry\tname\tvalue
                        if '\t' in cookie_content:
                            # Netscape cookie format
                            lines = cookie_content.split('\n')
                            cookie_count = 0
                            for line in lines:
                                if line.startswith('#') or not line.strip():
                                    continue
                                parts = line.split('\t')
                                if len(parts) >= 7:
                                    domain, _, path, _, expiry, name, value = parts[:7]
                                    self.session.cookies.set(name, value, domain=domain, path=path)
                                    cookie_count += 1
                            print(f"Using authentication cookie from: {cookie_file}")
                            return
                        elif '=' in cookie_content:
                            # Simple key=value format
                            key, value = cookie_content.split('=', 1)
                            self.session.cookies.set(key, value)
                            print(f"Using authentication cookie from: {cookie_file}")
                            return
                except Exception as e:
                    print(f"Warning: Failed to read cookie from {cookie_file}: {e}")
        
        print("Warning: No CERN SSO cookie found. Some MCM queries may fail.")
        print("To authenticate, please create a cookie file using:")
        print("  auth-get-sso-cookie -u https://cms-pdmv.cern.ch/mcm -o ~/.cern-sso-cookie.txt")
    
    def get_request(self, prepid: str) -> Optional[Dict]:
        """
        Get request information from MCM
        
        Args:
            prepid: The PrepID of the request
            
        Returns:
            Dictionary containing request information or None if failed
        """
        # First try public API
        public_result = self.get_request_public(prepid)
        if public_result:
            return public_result
        
        # Fallback to authenticated API
        url = f"{self.base_url}/restapi/requests/get/{prepid}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            # Check if response is JSON
            content_type = response.headers.get('content-type', '')
            if 'application/json' not in content_type:
                print(f"Error: Authentication failed or invalid response. Status: {response.status_code}")
                if 'text/html' in content_type:
                    print("Authentication appears to have failed. Please check your cookie.")
                return None
            
            data = response.json()
            
            if data.get('results'):
                return data['results']
            else:
                print(f"No results found for PrepID: {prepid}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching request {prepid}: {e}")
            return None
    
    def get_chain_request(self, prepid: str) -> Optional[List[Dict]]:
        """
        Get chain request information from MCM
        
        Args:
            prepid: The PrepID of the chain request
            
        Returns:
            List of requests in the chain or None if failed
        """
        # Note: Public API does not provide access to chain requests
        # The chain information (with actual PrepIDs) is only available through authenticated API
        
        # Fallback to authenticated API
        print("Trying authenticated API for chain...")
        url = f"{self.base_url}/restapi/chained_requests/get/{prepid}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            # Check if response is JSON
            content_type = response.headers.get('content-type', '')
            if 'application/json' not in content_type:
                print(f"Error: Expected JSON but got {content_type}")
                if 'text/html' in content_type:
                    print("Authentication appears to have failed for chain request")
                return None
            
            data = response.json()
            
            if data.get('results'):
                chain_data = data['results']
                
                # Get the chain of requests
                # The API returns 'chain' field with list of PrepIDs
                chain_ids = chain_data.get('chain', [])
                
                if chain_ids:
                    print(f"Found {len(chain_ids)} requests in chain")
                    requests_data = []
                    for req_id in chain_ids:
                        req_data = self.get_request(req_id)
                        if req_data:
                            requests_data.append(req_data)
                    
                    return requests_data
                else:
                    print("No chain PrepIDs found")
                    return None
            else:
                print(f"No results found for chain PrepID: {prepid}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching chain request {prepid}: {e}")
            return None
    
    def infer_wmLHEGEN_prepid_from_chain(self, chain_id: str, miniAOD_prepid: str) -> Optional[str]:
        """
        Infer the wmLHEGEN PrepID from chain ID
        
        Example:
        Chain: HIG-chain_RunIISummer20UL16wmLHEGEN_flow..._flowRunIISummer20UL16MiniAOD_flow...-01153
        -> wmLHEGEN: HIG-RunIISummer20UL16wmLHEGEN-01153
        """
        # Extract the physics group from chain ID
        parts = chain_id.split('-')
        if len(parts) < 2:
            return None
        
        physics_group = parts[0]  # e.g., "HIG"
        
        # Extract the number from the end of chain ID
        chain_parts = chain_id.split('-')
        if len(chain_parts) >= 2:
            number = chain_parts[-1]  # e.g., "01153"
        else:
            # Fallback to MiniAOD number
            miniAOD_parts = miniAOD_prepid.split('-')
            number = miniAOD_parts[-1] if len(miniAOD_parts) >= 3 else None
            if not number:
                return None
        
        # Look for wmLHEGEN or wmLHEGS in the chain
        if 'wmLHEGEN' in chain_id:
            # Extract the campaign name containing wmLHEGEN
            import re
            match = re.search(r'(RunII\w+wmLHEGEN|Run3\w+wmLHEGEN)', chain_id)
            if match:
                campaign = match.group(1)
                wmLHEGEN_prepid = f"{physics_group}-{campaign}-{number}"
                print(f"Inferred wmLHEGEN PrepID: {wmLHEGEN_prepid}")
                return wmLHEGEN_prepid
        elif 'wmLHEGS' in chain_id:
            # Handle wmLHEGS case
            match = re.search(r'(RunII\w+wmLHEGS|Run3\w+wmLHEGS)', chain_id)
            if match:
                campaign = match.group(1)
                wmLHEGS_prepid = f"{physics_group}-{campaign}-{number}"
                print(f"Inferred wmLHEGS PrepID: {wmLHEGS_prepid}")
                return wmLHEGS_prepid
        
        return None
    
    def search_requests_public(self, dataset_name: str) -> Optional[List[Dict]]:
        """
        Search using public API (no auth required)
        """
        import urllib.parse
        encoded_dataset = urllib.parse.quote(dataset_name, safe='')
        
        # Try the public search endpoint
        url = f"{self.base_url}/public/restapi/requests/produces/{encoded_dataset}"
        print(f"Trying public API: {url}")
        
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    data = response.json()
                    if 'results' in data:
                        results = data['results']
                        if isinstance(results, dict):
                            print("Success with public API!")
                            return [results]
                        elif isinstance(results, list):
                            print(f"Success with public API! Found {len(results)} result(s)")
                            return results
                    return None
            return None
        except Exception as e:
            print(f"Public API failed: {e}")
            return None

    def extract_wmLHEGEN_prepid_from_reqmgr(self, request_data: Dict) -> Optional[str]:
        """
        Extract wmLHEGEN/wmLHEGS PrepID from reqmgr_name entries (publicly available).

        This is a robust public fallback when chain fetching is unavailable.
        """
        import re
        reqmgr_names = request_data.get('reqmgr_name', []) or []
        if not isinstance(reqmgr_names, list):
            return None

        # Regex to capture e.g. B2G-RunIISummer20UL16wmLHEGENAPV-07713 or HIG-Run3Summer22EEwmLHEGS-00123
        pattern = re.compile(r"([A-Z]{2,3}-Run(?:II|3)\w*wmLHEG(?:EN|S)(?:APV)?-\d+)")

        for entry in reqmgr_names:
            name = entry.get('name') if isinstance(entry, dict) else str(entry)
            if not name:
                continue
            match = pattern.search(name)
            if match:
                found = match.group(1)
                print(f"Derived wmLHEG* PrepID from reqmgr_name: {found}")
                return found
        return None
    
    def get_request_public(self, prepid: str) -> Optional[Dict]:
        """
        Get request using public API
        """
        url = f"{self.base_url}/public/restapi/requests/get/{prepid}"
        print(f"Fetching {prepid} via public API")
        
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    data = response.json()
                    if data.get('results'):
                        return data['results']
            return None
        except Exception:
            return None
    
    def get_chained_request_from_dataset(self, dataset_name: str) -> Optional[str]:
        """
        Find the chained request ID for a given dataset
        
        Args:
            dataset_name: The dataset name
            
        Returns:
            Chained request ID or None if not found
        """
        # First try public API
        requests = self.search_requests_public(dataset_name)
        if not requests:
            # Fallback to authenticated API
            requests = self.search_requests(dataset_name)
            if not requests:
                return None
        
        # For datasets, usually there's one request
        request = requests[0] if isinstance(requests, list) else requests
        
        # Note: The "Chain" field containing actual PrepIDs is not available in the public API response
        # It's only available in the authenticated API when fetching chain requests directly
        
        # Check if there's a direct Chain or chain field with PrepIDs
        if 'Chain' in request and request['Chain']:
            print(f"Found 'Chain' field with PrepIDs")
            return request['Chain']  # Return the list of PrepIDs directly
        elif 'chain' in request and request['chain']:
            print(f"Found 'chain' field with PrepIDs")
            return request['chain']  # Return the list of PrepIDs directly
        
        # Otherwise use member_of_chain field which contains chain IDs
        chains = request.get('member_of_chain', [])
        if chains and len(chains) > 0:
            # Usually take the first chain
            chain_id = chains[0]
            print(f"Found chain ID in member_of_chain: {chain_id}")
            return chain_id
        else:
            print("No chain found for this dataset")
            return None
    
    def find_wmLHEGEN_in_chain(self, chain_requests: List[Dict]) -> Optional[Dict]:
        """
        Find the wmLHEGEN or wmLHEGS request in a chain
        
        Args:
            chain_requests: List of requests in the chain
            
        Returns:
            The wmLHEGEN/wmLHEGS request or None
        """
        for req in chain_requests:
            prepid = req.get('prepid', '')
            # Look for wmLHEGEN or wmLHEGS in the prepid
            if 'wmLHEGEN' in prepid or 'wmLHEGS' in prepid:
                print(f"Found wmLHEGEN/GS request: {prepid}")
                return req
        
        # If not found by name, look for GEN step
        for req in chain_requests:
            if req.get('dataset_name', '').endswith('/GEN'):
                print(f"Found GEN request: {req.get('prepid')}")
                return req
        
        return None
    
    def search_requests(self, dataset_name: str) -> Optional[List[Dict]]:
        """
        Search for requests by dataset name
        
        Args:
            dataset_name: The dataset name to search for
            
        Returns:
            List of matching requests or None if failed
        """
        # First try public API
        print("Trying public API first...")
        public_results = self.search_requests_public(dataset_name)
        if public_results:
            return public_results
        
        # Fallback to authenticated API
        print("\nPublic API failed, trying authenticated API...")
        url = f"{self.base_url}/restapi/requests/query"
        params = f"dataset_name={dataset_name}"
        full_url = f"{url}?{params}"
        
        print(f"Searching MCM at: {full_url}")
        
        try:
            # MCM expects the query as part of the URL, not as params
            response = self.session.get(full_url)
            response.raise_for_status()
            
            # Check if response is JSON
            content_type = response.headers.get('content-type', '')
            if 'application/json' not in content_type:
                print(f"Error: Authentication failed or invalid response. Status: {response.status_code}")
                if 'text/html' in content_type:
                    print("Authentication appears to have failed. Please check your cookie.")
                return None
            
            data = response.json()
            
            if data.get('results'):
                return data['results']
            else:
                print(f"No requests found for dataset: {dataset_name}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Error searching for dataset: {e}")
            return None


def extract_filter_efficiency(request_data: Dict) -> Dict[str, Union[float, str]]:
    """
    Extract filter efficiency information from MCM request data
    
    Args:
        request_data: Dictionary containing MCM request information
        
    Returns:
        Dictionary with filter efficiency information
    """
    result = {
        "prepid": request_data.get("prepid", ""),
        "dataset_name": request_data.get("dataset_name", ""),
        "filter_efficiency": None,
        "filter_efficiency_error": None,
        "generator_parameters": {},
        "notes": []
    }
    
    # Get filter efficiency
    filter_eff = request_data.get("filter_efficiency", None)
    filter_eff_error = request_data.get("filter_efficiency_error", None)
    
    if filter_eff is not None:
        result["filter_efficiency"] = filter_eff
        result["filter_efficiency_error"] = filter_eff_error
    
    # Get generator parameters that might contain additional efficiency info
    gen_params = request_data.get("generator_parameters", [])
    if gen_params:
        # Usually the last entry is the most recent
        if isinstance(gen_params, list) and len(gen_params) > 0:
            latest_gen_params = gen_params[-1]
        else:
            latest_gen_params = gen_params
        
        if isinstance(latest_gen_params, dict):
            # Extract relevant fields
            for key in ["filter_efficiency", "filter_efficiency_error", 
                       "match_efficiency", "match_efficiency_error", 
                       "cross_section", "negative_weights_fraction"]:
                if key in latest_gen_params and latest_gen_params[key] is not None:
                    result["generator_parameters"][key] = latest_gen_params[key]
                    
                    # If filter_efficiency is in generator_parameters and not at top level, promote it
                    if key == "filter_efficiency" and result["filter_efficiency"] is None:
                        result["filter_efficiency"] = latest_gen_params[key]
                    elif key == "filter_efficiency_error" and result["filter_efficiency_error"] is None:
                        result["filter_efficiency_error"] = latest_gen_params[key]
    
    # Check sequences for additional filter information
    sequences = request_data.get("sequences", [])
    if sequences:
        for seq in sequences:
            if isinstance(seq, dict):
                step = seq.get("step", "")
                if isinstance(step, str) and "filter" in step.lower():
                    result["notes"].append(f"Filter step found: {step}")
    
    # Get completion percentage
    completion = request_data.get("completed_events", 0)
    total = request_data.get("total_events", 0)
    if total > 0:
        result["completion_percentage"] = (completion / total) * 100
    
    return result


def print_efficiency_info(eff_info: Dict, verbose: bool = False):
    """
    Print filter efficiency information in a formatted way
    
    Args:
        eff_info: Dictionary containing efficiency information
        verbose: If True, print additional details
    """
    print("\n" + "="*60)
    print(f"PrepID: {eff_info['prepid']}")
    print(f"Dataset: {eff_info['dataset_name']}")
    print("-"*60)
    
    if eff_info["filter_efficiency"] is not None:
        print(f"Filter Efficiency: {eff_info['filter_efficiency']:.4f}")
        if eff_info["filter_efficiency_error"] is not None:
            print(f"Filter Efficiency Error: {eff_info['filter_efficiency_error']:.4f}")
    else:
        print("Filter Efficiency: Not found in request")
    
    if verbose and eff_info["generator_parameters"]:
        print("\nGenerator Parameters:")
        for key, value in eff_info["generator_parameters"].items():
            if value is not None:
                print(f"  {key}: {value}")
    
    if "completion_percentage" in eff_info:
        print(f"\nCompletion: {eff_info['completion_percentage']:.1f}%")
    
    if verbose and eff_info["notes"]:
        print("\nNotes:")
        for note in eff_info["notes"]:
            print(f"  - {note}")
    
    print("="*60)


def save_to_json(eff_info: Union[Dict, List[Dict]], output_file: str):
    """
    Save efficiency information to JSON file
    
    Args:
        eff_info: Efficiency information (single dict or list of dicts)
        output_file: Output JSON file path
    """
    with open(output_file, 'w') as f:
        json.dump(eff_info, f, indent=2)
    print(f"\nResults saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch filter efficiencies from CMS MCM (Monte Carlo Management)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch by PrepID:
  %(prog)s --prepid HIG-Run3Summer22EEwmLHEGS-00123
  
  # Fetch by dataset name:
  %(prog)s --dataset "/TTToHcToWAToMuMu_MHc-100_MA-15_MultiLepFilter_TuneCP5_13TeV*/MINIAODSIM"
  
  # Fetch chain request:
  %(prog)s --chain HIG-chain_Run3Summer22EEwmLHEGS_flowRun3Summer22EEDRPremix-00123
  
  # Save results to JSON:
  %(prog)s --prepid HIG-Run3Summer22EEwmLHEGS-00123 --output efficiency.json
  
  # Use verbose output:
  %(prog)s --prepid HIG-Run3Summer22EEwmLHEGS-00123 --verbose

Note: Filter efficiencies are typically stored in wmLHEGS/GEN requests, not MiniAOD.
"""
    )
    
    parser.add_argument("--prepid", help="MCM PrepID of the request")
    parser.add_argument("--dataset", help="Dataset name to search for")
    parser.add_argument("--chain", help="MCM chain PrepID")
    parser.add_argument("--output", "-o", help="Output JSON file to save results")
    parser.add_argument("--dev", action="store_true", help="Use development MCM instance")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print verbose output")
    
    args = parser.parse_args()
    
    if not any([args.prepid, args.dataset, args.chain]):
        parser.error("Please provide either --prepid, --dataset, or --chain")
    
    # Initialize MCM interface
    mcm = MCMInterface(dev=args.dev)
    
    results = []
    
    # Fetch by PrepID
    if args.prepid:
        print(f"Fetching request: {args.prepid}")
        request_data = mcm.get_request(args.prepid)
        if request_data:
            eff_info = extract_filter_efficiency(request_data)
            results.append(eff_info)
            print_efficiency_info(eff_info, verbose=args.verbose)
    
    # Fetch by dataset name
    elif args.dataset:
        print(f"Searching for dataset: {args.dataset}")

        # Preferred path: public MiniAOD request + reqmgr_name extraction of wmLHEGEN
        requests = mcm.search_requests(args.dataset)
        if requests and len(requests) > 0:
            miniAOD_req = requests[0]
            miniAOD_prepid = miniAOD_req.get('prepid', '')

            # Show MiniAOD info first
            eff_info = extract_filter_efficiency(miniAOD_req)
            results.append(eff_info)
            print_efficiency_info(eff_info, verbose=args.verbose)

            # Extract wmLHEGEN/wmLHEGS PrepID from reqmgr_name (public)
            wmLHEGEN_prepid = mcm.extract_wmLHEGEN_prepid_from_reqmgr(miniAOD_req)
            if not wmLHEGEN_prepid:
                # UL16 APV specific heuristic
                import re
                reqmgr = miniAOD_req.get('reqmgr_name', []) or []
                for entry in reqmgr:
                    name = entry.get('name') if isinstance(entry, dict) else str(entry)
                    if not name:
                        continue
                    m = re.search(r'(B2G-RunIISummer20UL16wmLHEGENAPV-\d+)', name)
                    if m:
                        wmLHEGEN_prepid = m.group(1)
                        print(f"Derived wmLHEGEN PrepID via UL16 APV heuristic: {wmLHEGEN_prepid}")
                        break

            if wmLHEGEN_prepid:
                print(f"\nFetching wmLHEGEN request: {wmLHEGEN_prepid}")
                wmLHEGEN_req = mcm.get_request(wmLHEGEN_prepid)
                if wmLHEGEN_req:
                    eff_info = extract_filter_efficiency(wmLHEGEN_req)
                    if eff_info['filter_efficiency'] or eff_info['generator_parameters'].get('filter_efficiency'):
                        print("\nFilter efficiency from wmLHEGEN request:")
                        results.append(eff_info)
                        print_efficiency_info(eff_info, verbose=args.verbose)
                    else:
                        print("No filter efficiency found in wmLHEGEN request")
                else:
                    print(f"Failed to fetch wmLHEGEN request: {wmLHEGEN_prepid}")
            else:
                # Fallback: try chain-based resolution with authentication
                chain_result = mcm.get_chained_request_from_dataset(args.dataset)
                chain_requests = None
                chain_id = None
                if chain_result:
                    if isinstance(chain_result, list):
                        print(f"\nFound chain with {len(chain_result)} PrepIDs directly")
                        chain_requests = []
                        for prepid in chain_result:
                            print(f"Fetching {prepid}...")
                            req_data = mcm.get_request(prepid)
                            if req_data:
                                chain_requests.append(req_data)
                    else:
                        chain_id = chain_result
                        print(f"\nFetching chain: {chain_id}")
                        chain_requests = mcm.get_chain_request(chain_id)

                if chain_requests:
                    print(f"Found {len(chain_requests)} request(s) in chain")
                    wmLHEGEN_req = mcm.find_wmLHEGEN_in_chain(chain_requests)
                    if wmLHEGEN_req:
                        eff_info = extract_filter_efficiency(wmLHEGEN_req)
                        if eff_info['filter_efficiency'] or eff_info['generator_parameters'].get('filter_efficiency'):
                            print("\nFilter efficiency from wmLHEGEN request:")
                            results.append(eff_info)
                            print_efficiency_info(eff_info, verbose=args.verbose)
                        else:
                            print("No filter efficiency found in wmLHEGEN request")
                    else:
                        print("No wmLHEGEN request found in chain")
                else:
                    print("Failed to resolve wmLHEGEN request via chain. Consider using --prepid or authenticating.")
        else:
            print("\nHint: If the dataset search fails, try:")
            print("1. Find the PrepID in MCM web interface: https://cms-pdmv.cern.ch/mcm")
            print("2. Use the PrepID directly: --prepid <PREPID>")
            print("3. Check if your cookie is still valid")
    
    # Fetch chain request
    elif args.chain:
        print(f"Fetching chain: {args.chain}")
        chain_requests = mcm.get_chain_request(args.chain)
        if chain_requests:
            print(f"Found {len(chain_requests)} request(s) in chain")
            for req in chain_requests:
                eff_info = extract_filter_efficiency(req)
                results.append(eff_info)
                print_efficiency_info(eff_info, verbose=args.verbose)
    
    # Save results if requested
    if args.output and results:
        save_data = results[0] if len(results) == 1 else results
        save_to_json(save_data, args.output)
    
    if not results:
        print("No results found")
        sys.exit(1)


if __name__ == "__main__":
    main()
