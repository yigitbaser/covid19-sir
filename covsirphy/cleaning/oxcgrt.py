#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
from covsirphy.cleaning.cbase import CleaningBase


class OxCGRTData(CleaningBase):
    """
    Data cleaning of OxCGRT dataset.
    """
    OXCGRT_VARIABLES = [
        "school_closing",
        "workplace_closing",
        "cancel_events",
        "gatherings_restrictions",
        "transport_closing",
        "stay_home_restrictions",
        "internal_movement_restrictions",
        "international_movement_restrictions",
        "information_campaigns",
        "testing_policy",
        "contact_tracing",
        "stringency_index"
    ]
    OXCGRT_COL_DICT = {v: v.capitalize() for v in OXCGRT_VARIABLES}
    OXCGRT_COLS = [
        CleaningBase.DATE, CleaningBase.COUNTRY, CleaningBase.ISO3,
        *list(OXCGRT_COL_DICT.values())
    ]
    OXCGRT_COLS_WITHOUT_COUNTRY = [
        CleaningBase.DATE, *list(OXCGRT_COL_DICT.values())
    ]

    def __init__(self, filename):
        super().__init__(filename)

    def cleaning(self):
        """
        Perform data cleaning of the raw data.
        This method overwrite super().cleaning() method.
        Policy indices (Overall etc.) are from
        README.md and documentation/index_methodology.md in
        https://github.com/OxCGRT/covid-policy-tracker/

        Returns:
            (pandas.DataFrame)
                Index:
                    reset index
                Columns:
                    - Date (pd.TimeStamp): Observation date
                    - Country (str): country/region name
                    - ISO3 (str): ISO 3166-1 alpha-3, like JPN
                    - other column names are defined by OxCGRTData.COL_DICT
        """
        df = self._raw.copy()
        # Rename the columns
        df = df.rename(self.OXCGRT_COL_DICT, axis=1)
        df = df.rename(
            {
                "CountryName": self.COUNTRY, "Date": self.DATE, "CountryCode": self.ISO3,
                "Country/Region": self.COUNTRY, "ObservationDate": self.DATE,
            },
            axis=1
        )
        # Confirm the expected columns are in raw data
        self.validate_dataframe(
            df, name="the raw data", columns=self.OXCGRT_COLS
        )
        # Read date records
        try:
            df[self.DATE] = pd.to_datetime(df[self.DATE], format="%Y%m%d")
        except ValueError:
            df[self.DATE] = pd.to_datetime(df[self.DATE], format="%Y-%m-%d")
        # Confirm float type
        float_cols = list(self.OXCGRT_COL_DICT.values())
        for col in float_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].fillna(method="ffill")
        # Select the columns to use
        df = df.loc[:, [self.DATE, self.COUNTRY, self.ISO3, *float_cols]]
        return df

    def subset(self, country=None, iso3=None):
        """
        Create a subset for a country.

        Notes:
            One of @country and @iso3 must be specified.

        Args:
            country (str): country name
            iso3 (str): ISO 3166-1 alpha-3, like JPN

        Returns:
            (pandas.DataFrame)
                Index:
                    reset index
                Columns:
                    - Date (pd.TimeStamp): Observation date
                    - other column names are defined by OxCGRTData.COL_DICT
        """
        df = self._cleaned_df.copy()
        if country is None and iso3 is None:
            raise ValueError("One of @country and @iso3 must be specified.")
        if iso3 is not None:
            if country is not None:
                raise ValueError("Either @country or @iso3 must be used.")
            iso_df = df.loc[:, [self.ISO3, self.COUNTRY]].drop_duplicates()
            iso_dict = iso_df.set_index(self.ISO3).to_dict()[self.COUNTRY]
            if iso3 not in iso_dict.keys():
                raise KeyError(f"@{iso3} is not included in this dataset.")
            country = iso_dict[iso3]
        df = df.loc[df[self.COUNTRY] == country, :]
        df = df.drop(
            [self.COUNTRY, self.ISO3], axis=1
        ).groupby(self.DATE).last()
        df = df.reset_index()
        if not df.empty:
            return df
        raise KeyError(f"@country {country} is not included in the dataset.")

    def total(self):
        """
        This is not defined for this child class.

        Raises:
            AttributeError: if called
        """
        raise AttributeError("OxCGRTData.total() is not defined.")
