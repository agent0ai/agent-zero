import asyncio
import time
from python.helpers import defer
from python.helpers.print_style import PrintStyle
import python.helpers.log as Log

class AutoNudgeMonitor:
    _instance = None
    _task = None

    @classmethod
    def start(cls):
        if cls._instance is None:
            cls._instance = AutoNudgeMonitor()
        if cls._task is None:
            cls._task = defer.DeferredTask(thread_name="AutoNudgeMonitor")
            cls._task.start_task(cls._instance._monitor_loop)

    @classmethod
    def stop(cls):
        if cls._task:
            cls._task.kill()
            cls._task = None

    async def _monitor_loop(self):
        from agent import AgentContext
        
        while True:
            try:
                await asyncio.sleep(5)  # Check every 5 seconds
                
                contexts = AgentContext.all()
                
                for context in contexts:
                    
                    if not context.config.auto_nudge_enabled:
                        continue
                    
                    if context.paused:
                        continue
                        
                    # Check if context has a running task
                    if not context.task or not context.task.is_alive():
                        continue
                        
                    # Check for timeout
                    if self._is_stuck(context):
                        self._trigger_nudge(context)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                # PrintStyle(font_color="red").print(f"AutoNudgeMonitor error: {e}")
                await asyncio.sleep(5)

    def _is_stuck(self, context) -> bool:
        # Get last activity timestamp
        last_activity = context.get_data("last_activity_time")
        
        if not last_activity:
            # If no activity recorded yet, skip
            return False
            
        # Check timeout
        timeout = context.config.auto_nudge_timeout
        elapsed = time.time() - last_activity
        
        if elapsed > timeout:
            return True
            
        return False

    def _trigger_nudge(self, context):
        PrintStyle(font_color="yellow").print(f"Auto-nudging context {context.id} due to inactivity")
        context.log.log(type="warning", content="Auto-nudge triggered due to inactivity.")
        
        # Reset activity timer to avoid immediate re-nudge
        context.set_data("last_activity_time", time.time())
        
        try:
            context.nudge()
        except Exception as e:
            PrintStyle(font_color="red").print(f"Failed to auto-nudge context {context.id}: {e}")
