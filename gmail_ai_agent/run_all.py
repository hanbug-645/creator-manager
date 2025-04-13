import multiprocessing
import os
import sys
import signal
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_main():
    """Run the main email processor"""
    from src.main import main
    main()

def run_web():
    """Run the web interface"""
    from src.web_interface import app
    app.run(debug=False, port=5050)

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    logger.info("Shutting down all processes...")
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Create processes
        main_process = multiprocessing.Process(target=run_main, name="EmailProcessor")
        web_process = multiprocessing.Process(target=run_web, name="WebInterface")
        
        logger.info("Starting Email Manager System...")
        
        # Start processes
        main_process.start()
        logger.info("Started Email Processor")
        
        web_process.start()
        logger.info("Started Web Interface")
        
        # Wait for processes to complete
        main_process.join()
        web_process.join()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal...")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
    finally:
        # Ensure processes are terminated
        if 'main_process' in locals() and main_process.is_alive():
            main_process.terminate()
        if 'web_process' in locals() and web_process.is_alive():
            web_process.terminate()
        logger.info("System shutdown complete.")
