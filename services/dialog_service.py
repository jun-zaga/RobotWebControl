class DialogService:
    def __init__(self, engine, runner, tts, rc, safety):
        self.engine = engine
        self.runner = runner
        self.tts = tts
        self.rc = rc
        self.safety = safety

    def process_text(self, text: str):
        reply = self.engine.process(text)

        if reply.interrupt:
            self.runner.interrupt_all()
            self.tts.stop()
            self.rc.stop()
            self.safety.update_last_cmd_ts()
            return {
                "ok": True,
                "matched": reply.matched,
                "state": reply.state,
                "speak": reply.text,
                "actions": [],
            }

        if reply.text:
            self.tts.say(reply.text)

        if reply.actions:
            self.runner.enqueue_actions(reply.actions)

        self.safety.update_last_cmd_ts()

        return {
            "ok": True,
            "matched": reply.matched,
            "state": reply.state,
            "speak": reply.text,
            "actions": reply.actions,
        }

    def run_script_demo(self):
        speak = "Script hook is wired. Add your scripted playback here."
        self.tts.say(speak)
        return {"ok": True, "state": self.engine.state.value, "speak": speak}