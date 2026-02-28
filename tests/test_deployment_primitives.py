from python.helpers.deployment_primitives import (
    execute_deployment,
    normalize_environment,
    record_deployment_result,
    run_predeployment_checks,
)


def test_normalize_environment_aliases():
    assert normalize_environment("prod") == "production"
    assert normalize_environment("stage") == "staging"
    assert normalize_environment("dev") == "development"
    assert normalize_environment("invalid") == ""


def test_run_predeployment_checks_structure():
    result = run_predeployment_checks("staging", skip_tests=True, skip_backup=False)
    assert result["environment"] == "staging"
    assert result["status"] == "passed"
    assert result["checks"]["tests"] is False
    assert result["checks"]["backup"] is True


def test_execute_and_record_deployment_result():
    execution = execute_deployment("development", platform="kubernetes")
    assert execution["status"] == "success"
    assert execution["platform"] == "kubernetes"
    assert execution["health_checks_passed"] is True

    record = record_deployment_result(execution)
    assert record["recorded"] is True
    assert record["summary"]["status"] == "success"
