#!/usr/bin/env python
"""
Send devices to their home position.

This script loads only the specified devices and their parent devices from an
ACQ4 configuration file, then commands each device to return to its home position.

This demonstrates selective device loading - a pattern that allows loading only
a subset of configured devices without starting the full ACQ4 system. This is
useful for:
- Command-line automation and testing
- Maintenance scripts that need specific hardware
- Reducing initialization time when only a subset of devices is needed

Usage:
    python home_devices.py --config myrig.cfg Stage Manipulator1 Manipulator2
    python home_devices.py -c myrig.cfg --log-level INFO Stage
    python home_devices.py -c myrig.cfg --speed 0.001 Stage  # 1 mm/s
    python home_devices.py -c myrig.cfg --speed slow --dry-run Stage

The script will:
1. Load only the specified devices and any parent devices they depend on
2. Call home() or goHome() on each device that supports homing
3. Report devices that don't support homing
4. Exit without starting the ACQ4 GUI

Note: This script does not require Qt event loop or GUI components to be running.
"""
import argparse
import logging
import sys
import time
from collections import OrderedDict

# Import acq4 components
import acq4
from acq4.Manager import Manager
from acq4.logging_config import setup_logging


def make_arg_parser():
    """Create argument parser for home_devices script.

    Includes relevant arguments from Manager.makeArgParser() plus device names.
    """
    parser = argparse.ArgumentParser(
        description='Send ACQ4 devices to their home position',
        epilog="""
Examples:
  %(prog)s --config myrig.cfg Stage Manipulator1
  %(prog)s -c myrig.cfg --log-level INFO Stage Manipulator1 Manipulator2
  %(prog)s -c myrig.cfg --speed 0.001 Stage  # Home at 1 mm/s
  %(prog)s -c myrig.cfg --speed slow --timeout 120 Stage
  %(prog)s -c myrig.cfg --dry-run Stage  # See what would happen

This script loads only the specified devices and their ancestors,
then sends each device to its home position using home() or goHome().
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Config file selection
    parser.add_argument(
        '--config', '-c',
        help='Configuration file to load',
        default=Manager._getConfigFile()
    )

    # Device selection
    parser.add_argument(
        'devices',
        nargs='+',
        metavar='DEVICE',
        help='Names of devices to send home (e.g., Stage, Manipulator1, etc.)'
    )

    # Logging options
    parser.add_argument(
        '--log-level',
        help='Set the console log level (DEBUG, INFO, WARNING, ERROR)',
        default='INFO'
    )
    parser.add_argument(
        '--root-log-level',
        help='Set the root log level',
        default='WARNING'
    )

    # Error handling
    parser.add_argument(
        '--exit-on-error', '-x',
        help='Exit immediately on first error during device initialization',
        action='store_true'
    )

    # Behavioral options
    parser.add_argument(
        '--speed',
        help='Speed setting for homing: "fast", "slow", or a numeric value in m/s',
        default='fast'
    )
    parser.add_argument(
        '--timeout',
        help='Maximum time to wait for each device to home (seconds)',
        type=float,
        default=60.0
    )
    parser.add_argument(
        '--dry-run',
        help='Show what would be done without actually homing devices',
        action='store_true'
    )

    return parser


def home_device(device, speed='fast', timeout=60.0, dry_run=False):
    """Send a single device to its home position.

    Parameters
    ----------
    device : Device
        The device instance to home
    speed : str or float
        Speed parameter to pass to homing method ('fast', 'slow', or numeric value in m/s)
    timeout : float
        Maximum time to wait for homing to complete (seconds)
    dry_run : bool
        If True, report what would be done but don't actually home

    Returns
    -------
    success : bool
        True if homing succeeded or was skipped gracefully
    message : str
        Description of what happened
    """
    dev_name = device.name()

    # Check for homing methods in order of preference
    if hasattr(device, 'goHome'):
        method_name = 'goHome'
        home_method = device.goHome
    elif hasattr(device, 'home'):
        method_name = 'home'
        home_method = device.home
    else:
        return True, f"Device '{dev_name}' does not support homing (no home() or goHome() method)"

    if dry_run:
        return True, f"[DRY RUN] Would call {dev_name}.{method_name}()"

    try:
        # Parse speed parameter - convert to float if it looks numeric
        parsed_speed = speed
        if isinstance(speed, str):
            try:
                parsed_speed = float(speed)
            except ValueError:
                # Keep as string ('fast' or 'slow')
                pass

        # Call the homing method
        # Some methods (like Stage.goHome) accept a speed parameter
        import inspect
        sig = inspect.signature(home_method)
        if 'speed' in sig.parameters:
            result = home_method(speed=parsed_speed)
        else:
            result = home_method()

        # Check if the result is a Future-like object that we need to wait for
        if result is not None and hasattr(result, 'wait'):
            start_time = time.time()
            while not result.isDone():
                if time.time() - start_time > timeout:
                    return False, f"Device '{dev_name}' homing timed out after {timeout}s"
                time.sleep(0.1)

        return True, f"Device '{dev_name}' sent to home position successfully"

    except Exception as e:
        return False, f"Error homing device '{dev_name}': {e}"


def main():
    """Main entry point for home_devices script."""
    parser = make_arg_parser()
    args = parser.parse_args()

    # Set up logging
    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    root_log_level = getattr(logging, args.root_log_level.upper(), logging.WARNING)
    setup_logging(None, gui=False, console_level=log_level, acq4_level=root_log_level)
    logger = logging.getLogger(__name__)

    logger.info("="*70)
    logger.info("ACQ4 Device Homing Script")
    logger.info("="*70)
    logger.info(f"Config file: {args.config}")
    logger.info(f"Devices to home: {', '.join(args.devices)}")
    if args.dry_run:
        logger.info("DRY RUN MODE - no devices will actually be homed")
    logger.info("="*70)

    # Create Manager instance without GUI
    # Note: We don't use Manager.runFromCommandLine() because that starts modules
    logger.info("Creating Manager instance...")
    manager = Manager()
    manager.exitOnError = args.exit_on_error

    # Read configuration (parse only, don't load devices yet)
    logger.info(f"Reading configuration from {args.config}...")
    import os
    manager.configDir = os.path.dirname(args.config)
    manager.readConfig(args.config, loadDevices=False)

    # Load only the specified devices and their ancestors
    logger.info(f"Loading devices: {args.devices}")
    try:
        loaded_devices = manager.loadDevicesSelective(args.devices)
    except Exception as e:
        logger.error(f"Failed to load devices: {e}", exc_info=True)
        return 1

    if not loaded_devices:
        logger.error("No devices were loaded successfully")
        return 1

    logger.info(f"Successfully loaded {len(loaded_devices)} device(s)")

    # Home each requested device (not the parent devices, just the ones requested)
    results = OrderedDict()
    for dev_name in args.devices:
        if dev_name not in loaded_devices:
            results[dev_name] = (False, f"Device '{dev_name}' was not loaded")
            continue

        device = loaded_devices[dev_name]
        logger.info(f"Homing device '{dev_name}'...")
        success, message = home_device(
            device,
            speed=args.speed,
            timeout=args.timeout,
            dry_run=args.dry_run
        )
        results[dev_name] = (success, message)

        # Log result
        if success:
            logger.info(f"  ✓ {message}")
        else:
            logger.error(f"  ✗ {message}")

    # Summary
    logger.info("="*70)
    logger.info("Summary:")
    logger.info("="*70)

    success_count = sum(1 for success, _ in results.values() if success)
    total_count = len(results)

    for dev_name, (success, message) in results.items():
        status = "SUCCESS" if success else "FAILED"
        logger.info(f"  {dev_name}: {status}")
        if not success:
            logger.info(f"    {message}")

    logger.info("="*70)
    logger.info(f"Completed: {success_count}/{total_count} devices homed successfully")
    logger.info("="*70)

    # Shutdown devices
    logger.info("Shutting down devices...")
    manager.quit()

    # Return exit code: 0 if all succeeded, 1 if any failed
    return 0 if success_count == total_count else 1


if __name__ == '__main__':
    try:
        exit_code = main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        exit_code = 130
    except Exception as e:
        logging.exception(f"Unexpected error: {e}")
        exit_code = 1

    sys.exit(exit_code)
