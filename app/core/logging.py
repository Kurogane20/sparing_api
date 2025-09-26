import logging, sys, json, time, uuid

class JsonFormatter(logging.Formatter):
    def format(self, record):
        base = {
            "level": record.levelname,
            "msg": record.getMessage(),
            "time": int(time.time() * 1000),
            "logger": record.name,
        }
        if hasattr(record, "request_id"):
            base["request_id"] = record.request_id
        if record.exc_info:
            base["exc"] = self.formatException(record.exc_info)
        return json.dumps(base, ensure_ascii=False)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())

logger = logging.getLogger("app")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
