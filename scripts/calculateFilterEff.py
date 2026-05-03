#!/usr/bin/env python3
"""
Script to calculate filter efficiencies for signal samples using GenXsecAnalyzer

This script:
1. Reads signal datasets from SampleLists/SignalMC_*.txt
2. Queries DAS for all file paths in each dataset
3. Runs cmsRun ana.py with all files to get GenXsecAnalyzer output
4. Parses the output to extract filter efficiency and cross section
5. Saves results to FilterEff/results_<era>.json

Usage:
    python3 scripts/calculateFilterEff.py --era 2016preVFP
    python3 scripts/calculateFilterEff.py --era 2017 --dry-run
    python3 scripts/calculateFilterEff.py --era all
    python3 scripts/calculateFilterEff.py --sample "/TTToHcToWAToMuMu_MHc-100_MA-15_.../MINIAODSIM"
"""

import argparse
import json
import subprocess
import sys
import os
import re
import multiprocessing
from pathlib import Path


# Worker functions for multiprocessing (must be at module level for pickling)

def extract_process_name(dataset):
    """Extract process name from dataset path"""
    parts = dataset.split('/')
    if len(parts) < 2:
        return None

    process_full = parts[1]
    # Extract up to and including MA-XX (handle both MA-135 and MA135 formats)
    match = re.match(r'(TTToHcToWAToMuMu_MHc-\d+_MA-?\d+)', process_full)
    if match:
        return match.group(1)

    return None


def query_das_files(dataset, dry_run=False):
    """Query DAS to get all files for a dataset"""
    cmd = [
        'dasgoclient',
        '--query', f'file dataset={dataset}'
    ]

    if dry_run:
        return []

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=300  # 5 minutes timeout
        )

        if result.returncode != 0:
            return []

        files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
        return files

    except subprocess.TimeoutExpired:
        return []
    except Exception:
        return []


def run_cmsrun(files, base_dir, dry_run=False, sample_mode=False):
    """Run cmsRun with GenXsecAnalyzer on all files"""
    if not files:
        return None

    file_list = ','.join(files)
    ana_py = Path(base_dir) / 'FilterEff/ana.py'

    if not ana_py.exists():
        return None

    if dry_run:
        return "DRY_RUN_OUTPUT"

    cmd = [
        'cmsRun',
        str(ana_py),
        f'inputFiles={file_list}',
        'maxEvents=-1'
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=7200  # 2 hour timeout
        )

        if result.returncode != 0:
            return None

        # Return combined stdout and stderr for parsing
        combined_output = result.stdout + "\n" + result.stderr
        return combined_output

    except subprocess.TimeoutExpired:
        return None
    except Exception:
        return None


def parse_genxsec_output(output):
    """Parse GenXsecAnalyzer output to extract filter efficiency and cross section"""
    if not output:
        return None

    result = {
        'filter_efficiency': None,
        'filter_efficiency_error': None,
        'cross_section': None,
        'cross_section_error': None,
        'total_events': None
    }

    # Parse filter efficiency (event-level)
    filter_eff_match = re.search(
        r'Filter efficiency \(event-level\)\s*=\s*\([^)]+\)\s*/\s*\([^)]+\)\s*=\s*([\d.eE+-]+)\s*\+-\s*([\d.eE+-]+)',
        output,
        re.IGNORECASE
    )
    if filter_eff_match:
        result['filter_efficiency'] = float(filter_eff_match.group(1))
        result['filter_efficiency_error'] = float(filter_eff_match.group(2))
    else:
        # Fallback pattern
        filter_eff_match = re.search(
            r'Filter efficiency.*?=\s*([\d.eE+-]+)\s*\+-\s*([\d.eE+-]+)',
            output,
            re.IGNORECASE
        )
        if filter_eff_match:
            result['filter_efficiency'] = float(filter_eff_match.group(1))
            result['filter_efficiency_error'] = float(filter_eff_match.group(2))

    # Parse cross section - try multiple patterns
    xsec_match = re.search(
        r'After filter:\s*(?:final\s+)?(?:total\s+)?cross section\s*=\s*([\d.eE+-]+)\s*\+-\s*([\d.eE+-]+)\s*pb',
        output,
        re.IGNORECASE
    )
    if not xsec_match:
        xsec_match = re.search(
            r'Before matching:\s*(?:total\s+)?cross section\s*=\s*([\d.eE+-]+)\s*\+-\s*([\d.eE+-]+)\s*pb',
            output,
            re.IGNORECASE
        )
    if not xsec_match:
        xsec_match = re.search(
            r'cross section\s*=\s*([\d.eE+-]+)\s*\+-\s*([\d.eE+-]+)\s*pb',
            output,
            re.IGNORECASE
        )
    if xsec_match:
        result['cross_section'] = float(xsec_match.group(1))
        result['cross_section_error'] = float(xsec_match.group(2))

    # Parse total events
    events_match = re.search(
        r'Total\s+(?:number\s+of\s+)?events\s*[=:]\s*(\d+)',
        output,
        re.IGNORECASE
    )
    if events_match:
        result['total_events'] = int(events_match.group(1))

    return result


def process_dataset_worker(args):
    """Worker function for multiprocessing - processes a single dataset"""
    dataset, base_dir, dry_run = args

    process_name = extract_process_name(dataset)
    if not process_name:
        return (dataset, None, f"Could not extract process name")

    # Query DAS for files
    files = query_das_files(dataset, dry_run)
    if not files:
        return (dataset, None, f"No files found for {process_name}")

    # Run cmsRun
    output = run_cmsrun(files, base_dir, dry_run, sample_mode=False)
    if not output:
        return (dataset, None, f"cmsRun failed for {process_name}")

    # Parse output
    if dry_run:
        result = {
            'filter_efficiency': 0.0,
            'cross_section': 0.0,
            'total_files': len(files),
            'total_events': 0
        }
    else:
        parsed = parse_genxsec_output(output)
        if not parsed or parsed['filter_efficiency'] is None:
            return (dataset, None, f"Could not parse filter efficiency for {process_name}")

        result = {
            'filter_efficiency': parsed['filter_efficiency'],
            'filter_efficiency_error': parsed['filter_efficiency_error'],
            'cross_section': parsed['cross_section'],
            'cross_section_error': parsed['cross_section_error'],
            'total_files': len(files),
            'total_events': parsed['total_events']
        }

    return (dataset, process_name, result)


class FilterEffCalculator:
    """Calculate filter efficiencies for signal samples"""

    def __init__(self, era=None, dry_run=False, sample_mode=False):
        self.era = era
        self.dry_run = dry_run
        self.sample_mode = sample_mode
        self.base_dir = Path(__file__).parent.parent.absolute()
        self.results = {}
        self.failed_datasets = []  # Track failed datasets for reporting

    def get_sample_list_path(self):
        """Get the path to the sample list file for the given era"""
        sample_list = self.base_dir / f"SampleLists/SignalMC_{self.era}.txt"
        if not sample_list.exists():
            raise FileNotFoundError(f"Sample list not found: {sample_list}")
        return sample_list

    def read_datasets(self):
        """Read datasets from sample list file"""
        sample_list = self.get_sample_list_path()
        datasets = []

        with open(sample_list, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line.startswith('#') or not line:
                    continue
                datasets.append(line)

        print(f"Found {len(datasets)} datasets in {sample_list.name}")
        return datasets

    def extract_process_name(self, dataset):
        """
        Extract process name from dataset path

        Example:
        /TTToHcToWAToMuMu_MHc-100_MA-15_MultiLepFilter_TuneCP5_13TeV-madgraph-pythia8/RunIISummer20UL16MiniAODAPVv2-.../MINIAODSIM
        -> TTToHcToWAToMuMu_MHc-100_MA-15
        """
        # Extract the first part before the campaign name
        parts = dataset.split('/')
        if len(parts) < 2:
            return None

        process_full = parts[1]  # e.g., TTToHcToWAToMuMu_MHc-100_MA-15_MultiLepFilter_TuneCP5_13TeV-madgraph-pythia8

        # Extract up to and including MA-XX (handle both MA-135 and MA135 formats)
        match = re.match(r'(TTToHcToWAToMuMu_MHc-\d+_MA-?\d+)', process_full)
        if match:
            return match.group(1)

        return None

    def query_das_files(self, dataset):
        """Query DAS to get all files for a dataset"""
        print(f"  Querying DAS for files...")

        cmd = [
            'dasgoclient',
            '--query', f'file dataset={dataset}'
        ]

        if self.dry_run:
            print(f"  [DRY RUN] Would execute: {' '.join(cmd)}")
            return []

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=300  # 5 minutes timeout
            )

            if result.returncode != 0:
                print(f"  ERROR: DAS query failed: {result.stderr}")
                return []

            files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
            print(f"  Found {len(files)} files")
            return files

        except subprocess.TimeoutExpired:
            print(f"  ERROR: DAS query timeout")
            return []
        except Exception as e:
            print(f"  ERROR: {e}")
            return []

    def run_cmsrun(self, files):
        """Run cmsRun with GenXsecAnalyzer on all files"""
        if not files:
            print("  ERROR: No files to process")
            return None

        # Prepare file list with proper formatting (comma-separated, with file: prefix)
        file_list = ','.join(files)

        ana_py = self.base_dir / 'FilterEff/ana.py'
        if not ana_py.exists():
            print(f"  ERROR: ana.py not found at {ana_py}")
            return None

        cmd = [
            'cmsRun',
            str(ana_py),
            f'inputFiles={file_list}',
            'maxEvents=-1'
        ]

        print(f"  Running cmsRun with {len(files)} files...")

        if self.dry_run:
            print(f"  [DRY RUN] Would execute: cmsRun {ana_py} inputFiles=<{len(files)} files> maxEvents=-1")
            return "DRY_RUN_OUTPUT"

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=7200  # 2 hour timeout
            )

            if result.returncode != 0:
                print(f"  ERROR: cmsRun failed with return code {result.returncode}")
                if self.sample_mode:
                    print(f"\n  FULL STDERR OUTPUT:")
                    print("="*80)
                    print(result.stderr)
                    print("="*80)
                else:
                    print(f"  STDERR (last 2000 chars): {result.stderr[-2000:]}")
                return None

            # In sample mode, print full output for debugging
            if self.sample_mode:
                print(f"\n  FULL STDOUT OUTPUT:")
                print("="*80)
                print(result.stdout)
                print("="*80)
                print(f"\n  FULL STDERR OUTPUT:")
                print("="*80)
                print(result.stderr)
                print("="*80)

            # Return combined stdout and stderr for parsing (GenXSecAnalyzer uses MessageLogger -> stderr)
            combined_output = result.stdout + "\n" + result.stderr
            return combined_output

        except subprocess.TimeoutExpired:
            print(f"  ERROR: cmsRun timeout (>2 hours)")
            return None
        except Exception as e:
            print(f"  ERROR: {e}")
            return None

    def parse_genxsec_output(self, output):
        """
        Parse GenXsecAnalyzer output to extract filter efficiency and cross section

        Example GenXSecAnalyzer output formats:
        Filter efficiency (event-level)= (58) / (5000) = 1.160e-02 +- 1.514e-03
        Before matching: total cross section = 1.234e+02 +- 5.678e+00 pb
        After filter: final cross section = 1.234e+02 +- 5.678e+00 pb
        """
        if not output:
            return None

        result = {
            'filter_efficiency': None,
            'filter_efficiency_error': None,
            'cross_section': None,
            'cross_section_error': None,
            'total_events': None
        }

        # Parse filter efficiency (event-level) - format from GenXSecAnalyzer
        # Example: Filter efficiency (event-level)= (58) / (5000) = 1.160e-02 +- 1.514e-03
        filter_eff_match = re.search(
            r'Filter efficiency \(event-level\)\s*=\s*\([^)]+\)\s*/\s*\([^)]+\)\s*=\s*([\d.eE+-]+)\s*\+-\s*([\d.eE+-]+)',
            output,
            re.IGNORECASE
        )
        if filter_eff_match:
            result['filter_efficiency'] = float(filter_eff_match.group(1))
            result['filter_efficiency_error'] = float(filter_eff_match.group(2))
        else:
            # Fallback: try simpler pattern without the fraction part
            filter_eff_match = re.search(
                r'Filter efficiency.*?=\s*([\d.eE+-]+)\s*\+-\s*([\d.eE+-]+)',
                output,
                re.IGNORECASE
            )
            if filter_eff_match:
                result['filter_efficiency'] = float(filter_eff_match.group(1))
                result['filter_efficiency_error'] = float(filter_eff_match.group(2))

        # Parse cross section - try multiple patterns
        # Pattern 1: "After filter: final cross section = X +- Y pb"
        xsec_match = re.search(
            r'After filter:\s*(?:final\s+)?(?:total\s+)?cross section\s*=\s*([\d.eE+-]+)\s*\+-\s*([\d.eE+-]+)\s*pb',
            output,
            re.IGNORECASE
        )
        if not xsec_match:
            # Pattern 2: "Before matching: total cross section = X +- Y pb"
            xsec_match = re.search(
                r'Before matching:\s*(?:total\s+)?cross section\s*=\s*([\d.eE+-]+)\s*\+-\s*([\d.eE+-]+)\s*pb',
                output,
                re.IGNORECASE
            )
        if not xsec_match:
            # Pattern 3: Generic "cross section = X +- Y pb"
            xsec_match = re.search(
                r'cross section\s*=\s*([\d.eE+-]+)\s*\+-\s*([\d.eE+-]+)\s*pb',
                output,
                re.IGNORECASE
            )
        if xsec_match:
            result['cross_section'] = float(xsec_match.group(1))
            result['cross_section_error'] = float(xsec_match.group(2))

        # Parse total events
        events_match = re.search(
            r'Total\s+(?:number\s+of\s+)?events\s*[=:]\s*(\d+)',
            output,
            re.IGNORECASE
        )
        if events_match:
            result['total_events'] = int(events_match.group(1))

        return result

    def process_dataset(self, dataset):
        """Process a single dataset"""
        process_name = self.extract_process_name(dataset)
        if not process_name:
            error_msg = f"Could not extract process name from {dataset}"
            print(f"ERROR: {error_msg}")
            self.failed_datasets.append((dataset, error_msg))
            return

        print(f"\n{'='*80}")
        print(f"Processing: {process_name}")
        print(f"Dataset: {dataset}")
        print(f"{'='*80}")

        # Query DAS for files
        files = self.query_das_files(dataset)
        if not files:
            error_msg = f"No files found for {process_name}"
            print(f"  Skipping {process_name} - no files found")
            self.failed_datasets.append((dataset, error_msg))
            return

        # Run cmsRun
        output = self.run_cmsrun(files)
        if not output:
            error_msg = f"cmsRun failed for {process_name}"
            print(f"  Skipping {process_name} - cmsRun failed")
            self.failed_datasets.append((dataset, error_msg))
            return

        # Parse output
        if self.dry_run:
            result = {
                'filter_efficiency': 0.0,
                'cross_section': 0.0,
                'total_files': len(files),
                'total_events': 0
            }
        else:
            parsed = self.parse_genxsec_output(output)
            if not parsed or parsed['filter_efficiency'] is None:
                error_msg = f"Could not parse filter efficiency from output for {process_name}"
                print(f"  WARNING: {error_msg}")
                if self.sample_mode:
                    print(f"\n  OUTPUT EXCERPT (last 2000 chars for debugging):")
                    print("="*80)
                    print(output[-2000:] if len(output) > 2000 else output)
                    print("="*80)
                self.failed_datasets.append((dataset, error_msg))
                return

            result = {
                'filter_efficiency': parsed['filter_efficiency'],
                'filter_efficiency_error': parsed['filter_efficiency_error'],
                'cross_section': parsed['cross_section'],
                'cross_section_error': parsed['cross_section_error'],
                'total_files': len(files),
                'total_events': parsed['total_events']
            }

        self.results[process_name] = result

        print(f"  SUCCESS!")
        print(f"    Filter efficiency: {result['filter_efficiency']:.6f}")
        if result.get('cross_section'):
            print(f"    Cross section: {result['cross_section']:.6f} pb")
        print(f"    Total files: {result['total_files']}")
        print(f"    Total events: {result.get('total_events', 'N/A')}")

        # Save incrementally after each successful dataset
        self.save_results_incremental(process_name)

    def get_output_file(self, process_name=None):
        """Get the output JSON file path"""
        output_dir = self.base_dir / 'FilterEff'
        output_dir.mkdir(exist_ok=True)

        if self.sample_mode and process_name:
            # For sample mode, use process name as filename
            return output_dir / f'sample_{process_name}.json'
        elif self.era:
            return output_dir / f'results_{self.era}.json'
        else:
            return output_dir / 'results_sample.json'

    def save_results_incremental(self, process_name=None):
        """Save results incrementally to JSON file (called after each successful dataset)"""
        output_file = self.get_output_file(process_name)

        # In sample mode, save only the current process
        if self.sample_mode and process_name:
            # Load existing results if file exists
            existing_results = {}
            if output_file.exists():
                with open(output_file, 'r') as f:
                    existing_results = json.load(f)

            # Merge with current result
            existing_results.update(self.results)

            with open(output_file, 'w') as f:
                json.dump(existing_results, f, indent=2)
        else:
            # Normal mode - overwrite entire file
            with open(output_file, 'w') as f:
                json.dump(self.results, f, indent=2)

    def save_results(self, show_summary=True):
        """Save results to JSON file (final save with summary)"""
        output_file = self.get_output_file()

        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        if show_summary:
            print(f"\n{'='*80}")
            print(f"Results saved to: {output_file}")
            print(f"Processed {len(self.results)} datasets successfully")
            if self.failed_datasets:
                print(f"Failed: {len(self.failed_datasets)} datasets")
            print(f"{'='*80}")

    def report_failed_datasets(self):
        """Report all failed datasets at the end"""
        if not self.failed_datasets:
            return

        print(f"\n{'='*80}")
        print(f"FAILED DATASETS ({len(self.failed_datasets)}):")
        print(f"{'='*80}")
        for dataset, error in self.failed_datasets:
            process_name = extract_process_name(dataset)
            print(f"\n  Dataset: {dataset}")
            if process_name:
                print(f"  Process: {process_name}")
            print(f"  Error: {error}")
        print(f"\n{'='*80}")

    def run(self, single_dataset=None, n_jobs=1):
        """Main execution method"""
        print(f"\n{'='*80}")
        print(f"Filter Efficiency Calculator")
        if single_dataset:
            print(f"Mode: Single dataset test")
            print(f"Dataset: {single_dataset}")
        else:
            print(f"Era: {self.era}")
        print(f"Dry run: {self.dry_run}")
        if n_jobs > 1:
            print(f"Parallel jobs: {n_jobs}")
        print(f"{'='*80}")

        # Determine datasets to process
        if single_dataset:
            datasets = [single_dataset]
        else:
            datasets = self.read_datasets()

        # Process datasets in parallel or serial
        if n_jobs > 1 and not single_dataset:
            self._run_parallel(datasets, n_jobs)
        else:
            self._run_serial(datasets, single_dataset)

        # Save final results and report failures
        if self.results:
            if not single_dataset:
                self.save_results()
                self.report_failed_datasets()
            else:
                # For single sample mode, save and print the result
                process_name = list(self.results.keys())[0] if self.results else None
                self.save_results()
                print(f"\n{'='*80}")
                print(f"Result for single dataset:")
                print(json.dumps(self.results, indent=2))
                if process_name:
                    output_file = self.get_output_file(process_name)
                    print(f"\nSaved to: {output_file}")
                print(f"{'='*80}")
        else:
            print("\nNo results to save")
            self.report_failed_datasets()

    def _run_serial(self, datasets, single_dataset=False):
        """Run dataset processing serially"""
        for i, dataset in enumerate(datasets, 1):
            if not single_dataset:
                print(f"\n[{i}/{len(datasets)}]")
            try:
                self.process_dataset(dataset)
            except Exception as e:
                error_msg = f"Unexpected exception: {str(e)}"
                print(f"ERROR processing dataset: {e}")
                import traceback
                traceback.print_exc()
                self.failed_datasets.append((dataset, error_msg))
                continue

    def _run_parallel(self, datasets, n_jobs):
        """Run dataset processing in parallel"""
        print(f"\nProcessing {len(datasets)} datasets with {n_jobs} parallel workers...")
        print("="*80)

        # Prepare arguments for worker processes
        worker_args = [(dataset, str(self.base_dir), self.dry_run) for dataset in datasets]

        # Create process pool and run workers
        completed = 0

        with multiprocessing.Pool(processes=n_jobs) as pool:
            # Use imap_unordered for progress tracking
            for dataset, process_name, result in pool.imap_unordered(process_dataset_worker, worker_args):
                completed += 1

                if isinstance(result, str):  # Error message
                    self.failed_datasets.append((dataset, result))
                    print(f"[{completed}/{len(datasets)}] FAILED: {result}")
                else:
                    self.results[process_name] = result
                    print(f"[{completed}/{len(datasets)}] SUCCESS: {process_name}")
                    print(f"    Filter efficiency: {result['filter_efficiency']:.6f}")
                    if result.get('cross_section'):
                        print(f"    Cross section: {result['cross_section']:.6f} pb")
                    print(f"    Total files: {result['total_files']}")

                    # Save incrementally after each successful dataset
                    self.save_results_incremental()

        # Print summary
        print("\n" + "="*80)
        print(f"Completed: {len(self.results)}/{len(datasets)} datasets")
        if self.failed_datasets:
            print(f"Failed: {len(self.failed_datasets)} datasets")
        print("="*80)


def main():
    parser = argparse.ArgumentParser(
        description="Calculate filter efficiencies for signal samples using GenXsecAnalyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process 2016 preVFP samples
  %(prog)s --era 2016preVFP

  # Process 2017 samples with dry run
  %(prog)s --era 2017 --dry-run

  # Process all eras
  %(prog)s --era all

  # Test single dataset (for debugging)
  %(prog)s --sample "/TTToHcToWAToMuMu_MHc-100_MA-15_.../MINIAODSIM"

  # Parallel processing with 8 workers
  %(prog)s --era 2016preVFP --jobs 8

  # Auto-detect number of CPUs
  %(prog)s --era 2016preVFP --jobs auto
"""
    )

    # Create mutually exclusive group for era and sample
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--era',
        choices=['2016preVFP', '2016postVFP', '2017', '2018', 'all'],
        help='Era to process'
    )
    group.add_argument(
        '--sample',
        help='Process a single dataset (for testing/debugging)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be executed without running cmsRun'
    )
    parser.add_argument(
        '--jobs', '-j',
        default='1',
        help='Number of parallel workers (default: 1, use "auto" for CPU count)'
    )

    args = parser.parse_args()

    # Parse number of jobs
    if args.jobs.lower() == 'auto':
        n_jobs = multiprocessing.cpu_count()
    else:
        try:
            n_jobs = int(args.jobs)
            if n_jobs < 1:
                parser.error("--jobs must be >= 1 or 'auto'")
        except ValueError:
            parser.error("--jobs must be an integer or 'auto'")

    # Handle single sample mode
    if args.sample:
        try:
            calculator = FilterEffCalculator(dry_run=args.dry_run, sample_mode=True)
            calculator.run(single_dataset=args.sample, n_jobs=1)  # Always single-threaded for sample mode
        except Exception as e:
            print(f"\nERROR processing sample: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        # Determine which eras to process
        if args.era == 'all':
            eras = ['2016preVFP', '2016postVFP', '2017', '2018']
        else:
            eras = [args.era]

        # Process each era
        for era in eras:
            try:
                calculator = FilterEffCalculator(era, dry_run=args.dry_run)
                calculator.run(n_jobs=n_jobs)
            except Exception as e:
                print(f"\nERROR processing era {era}: {e}")
                import traceback
                traceback.print_exc()
                continue

    print("\nDone!")


if __name__ == '__main__':
    main()
