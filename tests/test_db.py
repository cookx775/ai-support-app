from support_app.db import DatabaseConfigurationError, load_database_config

VALID_ENV = {
    "PGHOST": "ep-example.database.us-west-2.cloud.databricks.com",
    "PGDATABASE": "databricks_postgres",
    "PGUSER": "app-service-principal-id",
    "PGPORT": "5432",
    "PGSSLMODE": "require",
    "ENDPOINT_NAME": "projects/ai-support-app/branches/production/endpoints/primary",
}


def test_load_database_config_reads_lakebase_resource_environment():
    config = load_database_config(VALID_ENV)

    assert config.host == VALID_ENV["PGHOST"]
    assert config.endpoint_name == VALID_ENV["ENDPOINT_NAME"]
    assert "password" not in config.conninfo
    assert "sslmode=require" in config.conninfo


def test_load_database_config_reports_all_missing_required_values():
    try:
        load_database_config({})
    except DatabaseConfigurationError as error:
        assert "PGHOST" in str(error)
        assert "ENDPOINT_NAME" in str(error)
    else:
        raise AssertionError("Expected missing Lakebase settings to be rejected")


def test_load_database_config_rejects_unresolved_endpoint_placeholder():
    environment = {**VALID_ENV, "ENDPOINT_NAME": "REPLACE_WITH_LAKEBASE_ENDPOINT_NAME"}

    try:
        load_database_config(environment)
    except DatabaseConfigurationError as error:
        assert "ENDPOINT_NAME" in str(error)
    else:
        raise AssertionError("Expected endpoint placeholder to be rejected")
