from containup.business.audit.audit_report import AuditResult
from containup.business.reports.report_standard import report_standard
from containup.business.execution_listener import ExecutionListener
from containup.containup_cli import Config
from containup.stack.stack import Stack


class ReportGenerator:
    def __init__(self):
        pass

    def generate_report(
        self,
        stack: Stack,
        config: Config,
        listener: ExecutionListener,
        alerts: AuditResult,
    ) -> str:
        report: str = report_standard(
            execution_listener=listener, stack=stack, config=config, audit_report=alerts
        )
        return report
