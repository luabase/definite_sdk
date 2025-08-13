from typing import Any, Dict, Optional

import requests

SQL_ENDPOINT = "/v1/query"


class DefiniteSqlClient:
    """
    A SQL client for executing SQL queries via the Definite API.

    Initialization:
    >>> client = DefiniteClient("MY_API_KEY")
    >>> sql_client = client.get_sql_client()

    Executing SQL queries:
    >>> result = sql_client.execute("SELECT * FROM my_table LIMIT 10")
    >>> print(result)

    Executing SQL queries with integration ID:
    >>> result = sql_client.execute(
    ...     "SELECT * FROM my_table LIMIT 10",
    ...     integration_id="my_integration_id"
    ... )
    >>> print(result)

    Executing Cube queries:
    >>> cube_query = {
    ...     "dimensions": [],
    ...     "measures": ["sales.total_amount"],
    ...     "timeDimensions": [{"dimension": "sales.date", "granularity": "month"}],
    ...     "limit": 1000
    ... }
    >>> result = sql_client.execute_cube_query(
    ...     cube_query, integration_id="my_cube_integration"
    ... )
    >>> print(result)
    """

    def __init__(self, api_key: str, api_url: str):
        """
        Initializes the DefiniteSqlClient.

        Args:
            api_key (str): The API key for authorization.
            api_url (str): The base URL for the Definite API.
        """
        self._api_key = api_key
        self._sql_url = api_url + SQL_ENDPOINT

    def execute(self, sql: str, integration_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes a SQL query against a database integration.

        Args:
            sql (str): The SQL query to execute.
            integration_id (Optional[str]): The integration ID to query against.
                If not provided, the default integration will be used.

        Returns:
            Dict[str, Any]: The query result as returned by the API.

        Raises:
            requests.HTTPError: If the API request fails.

        Example:
            >>> result = sql_client.execute("SELECT COUNT(*) FROM users")
            >>> print(result)
        """
        payload: Dict[str, Any] = {"sql": sql}
        if integration_id:
            payload["integration_id"] = integration_id

        response = requests.post(
            self._sql_url,
            json=payload,
            headers={"Authorization": "Bearer " + self._api_key},
        )
        response.raise_for_status()
        return response.json()

    def execute_cube_query(
        self,
        cube_query: Dict[str, Any],
        integration_id: Optional[str] = None,
        persist: bool = True,
        invalidate: bool = False,
        raw: bool = False,
    ) -> Dict[str, Any]:
        """
        Executes a Cube query against a Cube integration.

        Args:
            cube_query (Dict[str, Any]): The Cube query in JSON format.
            integration_id (Optional[str]): The Cube integration ID to query against.
                If not provided, the default integration will be used.
            persist (bool): Whether to persist the query result to the cache.
            invalidate (bool): Whether to invalidate the cached result.
            raw (bool): Whether to return raw/unformatted cube results.

        Returns:
            Dict[str, Any]: The query result as returned by the API.

        Raises:
            requests.HTTPError: If the API request fails.

        Example:
            >>> cube_query = {
            ...     "dimensions": [],
            ...     "measures": ["sales.total_amount"],
            ...     "timeDimensions": [{
            ...         "dimension": "sales.date",
            ...         "granularity": "month",
            ...     }],
            ...     "limit": 1000
            ... }
            >>> result = sql_client.execute_cube_query(
            ...     cube_query, "my_cube_integration"
            ... )
            >>> print(result)

            >>> # To get raw/unformatted results:
            >>> raw_result = sql_client.execute_cube_query(
            ...     cube_query, "my_cube_integration", raw=True
            ... )
            >>> print(raw_result)
        """
        payload: Dict[str, Any] = {"cube_query": cube_query}
        if integration_id:
            payload["integration_id"] = integration_id
        if persist:
            payload["persist"] = persist
        if invalidate:
            payload["invalidate"] = invalidate

        # Build URL with query parameters
        url = self._sql_url
        if raw:
            url += "?raw=true"

        response = requests.post(
            url,
            json=payload,
            headers={"Authorization": "Bearer " + self._api_key},
        )
        response.raise_for_status()
        return response.json()
