"""Reusable list-query parameters: pagination, sorting, searching."""

from typing import Annotated, Literal

from fastapi import Depends, Query


class ListParams:
    def __init__(
        self,
        page: Annotated[int, Query(ge=1, description="1-based page number")] = 1,
        page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
        sort_by: Annotated[str | None, Query(description="Field to sort by")] = None,
        order: Annotated[Literal["asc", "desc"], Query(description="Sort direction")] = "asc",
        search: Annotated[str | None, Query(max_length=100, description="Search term")] = None,
    ):
        self.page = page
        self.page_size = page_size
        self.sort_by = sort_by
        self.order = order
        self.search = search


ListParamsDep = Annotated[ListParams, Depends()]
