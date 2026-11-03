"""
Great Expectations Quality Suites.
Defines explicit quality assertions and expectations for Bronze, Silver, and Gold datasets:
- expect_column_values_to_not_be_null
- expect_column_values_to_be_unique
- expect_column_values_to_be_between (positive prices & totals)
- expect_column_values_to_match_regex (email syntax)
- expect_column_values_to_be_in_set (status, segments, regions)
- expect_column_values_to_be_of_type
- expect_referential_integrity
"""
import re
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np


class QualityExpectationsSuite:
    """Executes Great Expectations assertions against DataFrames."""

    @staticmethod
    def expect_column_to_exist(df: pd.DataFrame, column: str) -> Dict[str, Any]:
        success = column in df.columns
        return {
            "expectation": "expect_column_to_exist",
            "column": column,
            "success": success,
            "details": f"Column '{column}' exists in dataset." if success else f"Column '{column}' missing!"
        }

    @staticmethod
    def expect_column_values_to_not_be_null(df: pd.DataFrame, column: str) -> Dict[str, Any]:
        if column not in df.columns:
            return {"expectation": "expect_column_values_to_not_be_null", "column": column, "success": False, "details": "Column missing"}
        null_count = int(df[column].isnull().sum())
        success = null_count == 0
        return {
            "expectation": "expect_column_values_to_not_be_null",
            "column": column,
            "success": success,
            "unexpected_count": null_count,
            "unexpected_percent": round(null_count / len(df) * 100, 2) if len(df) > 0 else 0,
            "details": f"{null_count} null values found" if not success else "No null values found"
        }

    @staticmethod
    def expect_column_values_to_be_unique(df: pd.DataFrame, column: str) -> Dict[str, Any]:
        if column not in df.columns:
            return {"expectation": "expect_column_values_to_be_unique", "column": column, "success": False, "details": "Column missing"}
        dup_count = int(df[column].duplicated().sum())
        success = dup_count == 0
        return {
            "expectation": "expect_column_values_to_be_unique",
            "column": column,
            "success": success,
            "unexpected_count": dup_count,
            "unexpected_percent": round(dup_count / len(df) * 100, 2) if len(df) > 0 else 0,
            "details": f"{dup_count} duplicate keys detected" if not success else "All keys unique"
        }

    @staticmethod
    def expect_column_values_to_be_between(df: pd.DataFrame, column: str, min_value: float, max_value: float) -> Dict[str, Any]:
        if column not in df.columns:
            return {"expectation": "expect_column_values_to_be_between", "column": column, "success": False, "details": "Column missing"}
        bad_mask = (df[column] < min_value) | (df[column] > max_value)
        bad_count = int(bad_mask.sum())
        success = bad_count == 0
        return {
            "expectation": "expect_column_values_to_be_between",
            "column": column,
            "success": success,
            "min_value": min_value,
            "max_value": max_value,
            "unexpected_count": bad_count,
            "unexpected_percent": round(bad_count / len(df) * 100, 2) if len(df) > 0 else 0,
            "details": f"{bad_count} values outside [{min_value}, {max_value}]" if not success else "All values within bounds"
        }

    @staticmethod
    def expect_column_values_to_be_in_set(df: pd.DataFrame, column: str, value_set: List[str]) -> Dict[str, Any]:
        if column not in df.columns:
            return {"expectation": "expect_column_values_to_be_in_set", "column": column, "success": False, "details": "Column missing"}
        bad_mask = ~df[column].isin(value_set)
        bad_count = int(bad_mask.sum())
        success = bad_count == 0
        return {
            "expectation": "expect_column_values_to_be_in_set",
            "column": column,
            "success": success,
            "unexpected_count": bad_count,
            "unexpected_percent": round(bad_count / len(df) * 100, 2) if len(df) > 0 else 0,
            "details": f"{bad_count} values outside allowed set" if not success else "All values in permitted set"
        }

    @staticmethod
    def expect_column_values_to_match_regex(df: pd.DataFrame, column: str, regex: str) -> Dict[str, Any]:
        if column not in df.columns:
            return {"expectation": "expect_column_values_to_match_regex", "column": column, "success": False, "details": "Column missing"}
        bad_mask = ~df[column].astype(str).str.match(regex)
        bad_count = int(bad_mask.sum())
        success = bad_count == 0
        return {
            "expectation": "expect_column_values_to_match_regex",
            "column": column,
            "success": success,
            "unexpected_count": bad_count,
            "unexpected_percent": round(bad_count / len(df) * 100, 2) if len(df) > 0 else 0,
            "details": f"{bad_count} values failed regex pattern" if not success else "All values matched pattern"
        }

    @staticmethod
    def expect_referential_integrity(child_df: pd.DataFrame, child_col: str, parent_df: pd.DataFrame, parent_col: str) -> Dict[str, Any]:
        parent_keys = set(parent_df[parent_col].dropna().unique())
        orphan_mask = ~child_df[child_col].isin(parent_keys)
        orphan_count = int(orphan_mask.sum())
        success = orphan_count == 0
        return {
            "expectation": "expect_referential_integrity",
            "child_column": child_col,
            "parent_column": parent_col,
            "success": success,
            "unexpected_count": orphan_count,
            "unexpected_percent": round(orphan_count / len(child_df) * 100, 2) if len(child_df) > 0 else 0,
            "details": f"{orphan_count} orphaned foreign keys detected" if not success else "Referential integrity intact"
        }
