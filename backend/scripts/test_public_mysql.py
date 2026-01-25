import pymysql
import sys
import time
import logging
import json
import traceback
from datetime import datetime

# Configure Logging to output structured logs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(message)s', # We will format the message as JSON manually
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("MySQLMonitor")

def log_structured(event_type, status, **kwargs):
    """
    Helper to log structured JSON events
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "event": event_type,
        "status": status,
        **kwargs
    }
    # Use json.dumps for clean output
    logger.info(json.dumps(entry, ensure_ascii=False, default=str))

def test_rfam_monitor(duration_seconds=60, interval_seconds=5):
    """
    Connects to Rfam public database and monitors connection health.
    """
    host = 'mysql-rfam-public.ebi.ac.uk'
    port = 4497
    user = 'rfamro'
    password = ''
    database = 'Rfam'
    
    print(f"--- Starting MySQL Monitor for {host}:{port} ---")
    print(f"--- Duration: {duration_seconds}s, Interval: {interval_seconds}s ---\n")

    log_structured("CONNECTION_INIT", "PENDING", config={"host": host, "port": port, "user": user, "db": database})
    
    connection = None
    start_time = time.time()
    
    try:
        # 1. Connection Establishment & Handshake
        t0 = time.time()
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            port=port,
            database=database,
            connect_timeout=10,
            read_timeout=30,
            write_timeout=30,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        t1 = time.time()
        handshake_duration = (t1 - t0) * 1000
        
        server_info = connection.get_server_info()
        log_structured("CONNECTION_HANDSHAKE", "SUCCESS", 
                      duration_ms=round(handshake_duration, 2), 
                      server_version=server_info)

        # 2. Initial Verification
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION(), CURRENT_USER(), NOW()")
            result = cursor.fetchone()
            log_structured("INITIAL_QUERY", "SUCCESS", result=result)

        # 3. Heartbeat Monitoring Loop
        loops = 0
        log_structured("MONITOR_LOOP", "STARTED")
        
        while (time.time() - start_time) < duration_seconds:
            loops += 1
            loop_start = time.time()
            
            try:
                # Check connection status using ping
                # reconnect=False ensures we test the current connection stability
                connection.ping(reconnect=False)
                ping_latency = (time.time() - loop_start) * 1000
                
                log_structured("HEARTBEAT", "ALIVE", 
                              seq=loops, 
                              latency_ms=round(ping_latency, 2))
                
                # Execute a lightweight query to verify read capability
                with connection.cursor() as cursor:
                    q_start = time.time()
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                    query_latency = (time.time() - q_start) * 1000
                    
                    if loops % 5 == 0: # Log query success every 5 loops to reduce noise
                        log_structured("QUERY_TEST", "SUCCESS", 
                                      seq=loops, 
                                      latency_ms=round(query_latency, 2))

            except Exception as e:
                # 4. Capture Network/Connection Errors in Loop
                log_structured("HEARTBEAT", "FAILED", 
                              seq=loops, 
                              error=str(e), 
                              error_type=type(e).__name__)
                logger.error(f"Stack Trace:\n{traceback.format_exc()}")
                raise e # Stop monitoring if connection breaks
            
            time.sleep(interval_seconds)

        log_structured("MONITOR_LOOP", "COMPLETED", total_duration_s=round(time.time() - start_time, 2))

    except pymysql.MySQLError as e:
        # 5. Detailed MySQL Error Handling
        # pymysql exceptions usually have args (code, message)
        error_code = e.args[0] if len(e.args) > 0 else "UNKNOWN"
        error_msg = e.args[1] if len(e.args) > 1 else str(e)
        
        log_structured("CONNECTION_ERROR", "CRITICAL", 
                      error_code=error_code, 
                      error_message=error_msg)
        logger.error(f"Full Stack Trace:\n{traceback.format_exc()}")
        
    except Exception as e:
        # General Exceptions
        log_structured("SYSTEM_ERROR", "CRITICAL", 
                      error_type=type(e).__name__, 
                      error_message=str(e))
        logger.error(f"Full Stack Trace:\n{traceback.format_exc()}")
        
    finally:
        # Cleanup
        if connection:
            try:
                connection.close()
                log_structured("CONNECTION_CLOSE", "SUCCESS")
            except Exception as e:
                log_structured("CONNECTION_CLOSE", "ERROR", error=str(e))

if __name__ == "__main__":
    # Monitor for 10 seconds for quick test
    test_rfam_monitor(duration_seconds=10, interval_seconds=2)
