# Terminal monitor to show whats happening during a run

We have a terminal monitor and a run command, but they are currently hooked up so when running the user can see. The monitor will likely need to be on a seperate thread, with something like
monitor_thread = threading.Thread(target=monitor.run, daemon=True)
monitor_thread.start()

Lets add a CLI option that allows the user to see the current execution using the terminal monitor
