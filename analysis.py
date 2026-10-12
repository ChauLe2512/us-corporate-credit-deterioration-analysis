import pandas as pd
from pathlib import Path



# ============================================================
# 1. DATA LOADING AND SAMPLE CONSTRUCTION
# ============================================================

# Compustat data are not distributed with this repository.
# Licensed source files should be placed locally in data_raw/.
DATA_DIR = Path("data_raw")

file1 = DATA_DIR / "compustat_fundamentals_annual_2009_2017.csv"
file2 = DATA_DIR / "compustat_fundamentals_annual_2018_2025.csv"

df1 = pd.read_csv(file1, low_memory=False)
df2 = pd.read_csv(file2, low_memory=False)

print("Input shapes:")
print("2009–2017:", df1.shape)
print("2018–2025:", df2.shape)
print("Columns identical:", df1.columns.equals(df2.columns))


# Combine files and restrict analysis period to 2010–2024
df = pd.concat([df1, df2], ignore_index=True)

df = df[
    (df["fyear"] >= 2010) &
    (df["fyear"] <= 2024)
].copy()

print("\nCombined sample:", df.shape)
print("Fiscal-year range:", df["fyear"].min(), "-", df["fyear"].max())


# ------------------------------------------------------------
# Initial data checks
# ------------------------------------------------------------

print("\nCompustat reporting settings:")
for col in ["costat", "curcd", "datafmt", "indfmt", "consol"]:
    print(f"\n{col}")
    print(df[col].value_counts(dropna=False))


# Check duplicate company-year observations
duplicates = df.duplicated(
    subset=["gvkey", "fyear"],
    keep=False
)

print("\nRows involved in duplicate GVKEY-FYEAR combinations:")
print(duplicates.sum())

print("\nExample duplicate observations:")
print(
    df.loc[
        duplicates,
        ["gvkey", "conm", "fyear", "datadate",
         "fic", "curcd", "indfmt", "costat"]
    ]
    .sort_values(["gvkey", "fyear", "datadate"])
    .head(20)
)


# Variables required for the financial-ratio analysis
ratio_variables = [
    "gvkey", "conm", "fyear", "sich", "naics",
    "sale", "ebit", "ebitda", "ni",
    "act", "lct", "at", "dlc", "dltt", "ceq",
    "xint", "oancf"
]

print("\nMissing values before sample filtering:")
print(df[ratio_variables].isna().sum())

print("\nCountry of incorporation:")
print(df["fic"].value_counts(dropna=False))

print("\nExact duplicate rows:")
print(df.duplicated().sum())


# ------------------------------------------------------------
# Construct U.S. non-financial corporate sample
# ------------------------------------------------------------

analysis_df = df[
    (df["fic"] == "USA") &
    (df["curcd"] == "USD") &
    (df["indfmt"] == "INDL") &
    (df["datafmt"] == "STD") &
    (df["consol"] == "C")
].copy()

print("\nSample after Compustat reporting filters:")
print(analysis_df.shape)


# Exclude Finance and Insurance (NAICS sector 52)
naics_text = analysis_df["naics"].astype("Int64").astype("string")
financial_firm = naics_text.str.startswith("52", na=False)

print("Financial-sector rows excluded:", financial_firm.sum())

analysis_df = analysis_df[~financial_firm].copy()

print("Sample after excluding financial firms:")
print(analysis_df.shape)


# ------------------------------------------------------------
# Resolve remaining duplicate company-years
# ------------------------------------------------------------

duplicates_clean = analysis_df.duplicated(
    subset=["gvkey", "fyear"],
    keep=False
)

print("\nDuplicate company-year rows remaining:")
print(duplicates_clean.sum())

print("\nExample remaining duplicates:")
print(
    analysis_df.loc[
        duplicates_clean,
        ["gvkey", "conm", "fyear", "datadate", "naics"]
    ]
    .sort_values(["gvkey", "fyear", "datadate"])
    .head(20)
)


# Keep the observation with the latest reporting date
# when multiple observations exist for the same company-year.
analysis_df["datadate"] = pd.to_datetime(
    analysis_df["datadate"],
    errors="coerce"
)

analysis_df = (
    analysis_df
    .sort_values(
        ["gvkey", "fyear", "datadate"],
        na_position="first"
    )
    .drop_duplicates(
        subset=["gvkey", "fyear"],
        keep="last"
    )
    .copy()
)

print("\nFinal cleaned analytical sample:")
print(analysis_df.shape)

print("Remaining duplicate company-years:")
print(
    analysis_df.duplicated(
        subset=["gvkey", "fyear"]
    ).sum()
)


# ------------------------------------------------------------
# Final missing-data diagnostic
# ------------------------------------------------------------

ratio_variables_final = [
    "sale", "ebit", "ebitda", "ni",
    "act", "lct", "at",
    "dlc", "dltt", "ceq",
    "xint", "oancf"
]

print("\nMissing values in final analytical sample:")
print(analysis_df[ratio_variables_final].isna().sum())

print("\nTotal analytical observations:")
print(len(analysis_df))



# ============================================================
# 2. FINANCIAL RATIO CONSTRUCTION AND WINSORIZATION
# ============================================================

# Total Debt = Short-term Debt (DLC) + Long-term Debt (DLTT)
# If either component is missing, Total Debt remains missing.
analysis_df["total_debt"] = (
    analysis_df["dlc"] + analysis_df["dltt"]
)


# ------------------------------------------------------------
# Financial-ratio calculation
# ------------------------------------------------------------

# Ratios are calculated only when the denominator is positive.
# Negative numerators are retained because they may contain
# economically relevant information.
def safe_ratio(numerator, denominator):
    return numerator.div(denominator).where(denominator > 0)


# Profitability
analysis_df["ebitda_margin"] = safe_ratio(
    analysis_df["ebitda"],
    analysis_df["sale"]
)

analysis_df["ebit_margin"] = safe_ratio(
    analysis_df["ebit"],
    analysis_df["sale"]
)

analysis_df["roa"] = safe_ratio(
    analysis_df["ni"],
    analysis_df["at"]
)


# Liquidity
analysis_df["current_ratio"] = safe_ratio(
    analysis_df["act"],
    analysis_df["lct"]
)


# Leverage
analysis_df["debt_assets"] = safe_ratio(
    analysis_df["total_debt"],
    analysis_df["at"]
)

analysis_df["debt_equity"] = safe_ratio(
    analysis_df["total_debt"],
    analysis_df["ceq"]
)

analysis_df["debt_ebitda"] = safe_ratio(
    analysis_df["total_debt"],
    analysis_df["ebitda"]
)


# Debt-servicing capacity
analysis_df["interest_coverage"] = safe_ratio(
    analysis_df["ebit"],
    analysis_df["xint"]
)


# Cash-flow capacity
analysis_df["ocf_debt"] = safe_ratio(
    analysis_df["oancf"],
    analysis_df["total_debt"]
)


ratios = [
    "ebitda_margin",
    "ebit_margin",
    "roa",
    "current_ratio",
    "debt_assets",
    "debt_equity",
    "debt_ebitda",
    "interest_coverage",
    "ocf_debt"
]


# ------------------------------------------------------------
# Ratio diagnostics
# ------------------------------------------------------------

print("\nValid observations by ratio:")
print(analysis_df[ratios].notna().sum())

print("\nRatio summary:")
print(analysis_df[ratios].describe())

print("\nRatio quantiles before winsorization:")
print(
    analysis_df[ratios].quantile(
        [0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99]
    )
)


# ------------------------------------------------------------
# Annual winsorization
# ------------------------------------------------------------

# Preserve the original ratios and create separate winsorized
# versions for deterioration tests, peer comparisons and visualization.
# Each ratio is capped at its fiscal-year 1st and 99th percentiles.
for ratio in ratios:
    lower = analysis_df.groupby("fyear")[ratio].transform(
        lambda x: x.quantile(0.01)
    )

    upper = analysis_df.groupby("fyear")[ratio].transform(
        lambda x: x.quantile(0.99)
    )

    analysis_df[ratio + "_w"] = analysis_df[ratio].clip(
        lower=lower,
        upper=upper
    )


# ------------------------------------------------------------
# Fundamental warning indicators
# ------------------------------------------------------------

# Missing financial information remains missing rather than
# being interpreted as the absence of a warning.
analysis_df["negative_ebitda"] = (
    analysis_df["ebitda"]
    .lt(0)
    .where(analysis_df["ebitda"].notna())
    .astype("boolean")
)

analysis_df["negative_equity"] = (
    analysis_df["ceq"]
    .lt(0)
    .where(analysis_df["ceq"].notna())
    .astype("boolean")
)

analysis_df["negative_ocf"] = (
    analysis_df["oancf"]
    .lt(0)
    .where(analysis_df["oancf"].notna())
    .astype("boolean")
)

print("\nFundamental warnings:")
print("Negative EBITDA:", analysis_df["negative_ebitda"].sum())
print("Negative equity:", analysis_df["negative_equity"].sum())
print("Negative operating cash flow:", analysis_df["negative_ocf"].sum())



# ============================================================
# 3. INDUSTRY PEER BENCHMARKS AND YEAR-OVER-YEAR TRENDS
# ============================================================

# ------------------------------------------------------------
# Construct 3-digit NAICS industry groups
# ------------------------------------------------------------

analysis_df["naics3"] = (
    analysis_df["naics"]
    .astype("Int64")
    .astype("string")
    .str[:3]
)

print("\nNumber of 3-digit NAICS industries:")
print(analysis_df["naics3"].nunique())


# Winsorized ratios used for deterioration and peer analysis
ratios_w = [
    "ebitda_margin_w",
    "ebit_margin_w",
    "roa_w",
    "current_ratio_w",
    "debt_assets_w",
    "debt_equity_w",
    "debt_ebitda_w",
    "interest_coverage_w",
    "ocf_debt_w"
]


# ------------------------------------------------------------
# Industry-year peer benchmarks
# ------------------------------------------------------------

# For each ratio, calculate the median among firms in the same
# 3-digit NAICS industry and fiscal year.
#
# Peer benchmarks are retained only when at least 20 valid
# observations are available for the relevant ratio.

for ratio in ratios_w:
    peer_group = analysis_df.groupby(
        ["fyear", "naics3"]
    )[ratio]

    peer_median = peer_group.transform("median")
    peer_count = peer_group.transform("count")

    analysis_df[ratio + "_peer_count"] = peer_count

    analysis_df[ratio + "_peer_median"] = (
        peer_median.where(peer_count >= 20)
    )


print("\nPeer-analysis sample shape:")
print(analysis_df.shape)

print("\nExample peer benchmark:")
print(
    analysis_df[
        [
            "conm",
            "fyear",
            "naics3",
            "ebitda_margin_w",
            "ebitda_margin_w_peer_median",
            "ebitda_margin_w_peer_count"
        ]
    ].head(20)
)


# ------------------------------------------------------------
# Year-over-year changes
# ------------------------------------------------------------

# Sort each company's observations chronologically.
analysis_df = (
    analysis_df
    .sort_values(["gvkey", "fyear"])
    .copy()
)

# Identify the previous available fiscal year for each company.
analysis_df["previous_fyear"] = (
    analysis_df.groupby("gvkey")["fyear"].shift(1)
)

# A year-over-year comparison is valid only when the previous
# observation is exactly one fiscal year earlier.
analysis_df["consecutive_year"] = (
    analysis_df["fyear"] -
    analysis_df["previous_fyear"] == 1
)

# Calculate year-over-year changes only for consecutive years.
for ratio in ratios_w:
    previous_value = (
        analysis_df.groupby("gvkey")[ratio].shift(1)
    )

    analysis_df[ratio + "_yoy_change"] = (
        analysis_df[ratio] - previous_value
    ).where(analysis_df["consecutive_year"])


# ------------------------------------------------------------
# Distance from industry peer median
# ------------------------------------------------------------

# Peer gap = company ratio - industry-year median.
#
# For profitability, liquidity, interest coverage and cash-flow
# ratios, a negative peer gap indicates weaker performance.
#
# For leverage ratios, a positive peer gap indicates weaker
# performance.
for ratio in ratios_w:
    analysis_df[ratio + "_peer_gap"] = (
        analysis_df[ratio] -
        analysis_df[ratio + "_peer_median"]
    )


# ------------------------------------------------------------
# Diagnostic example
# ------------------------------------------------------------

example_gvkey = analysis_df["gvkey"].iloc[0]

print("\nExample company trend and peer comparison:")
print(
    analysis_df.loc[
        analysis_df["gvkey"] == example_gvkey,
        [
            "conm",
            "fyear",
            "ebitda_margin_w",
            "ebitda_margin_w_yoy_change",
            "ebitda_margin_w_peer_median",
            "ebitda_margin_w_peer_gap",
            "debt_ebitda_w",
            "debt_ebitda_w_yoy_change",
            "debt_ebitda_w_peer_median",
            "debt_ebitda_w_peer_gap"
        ]
    ]
)



# ============================================================
# 4. DETERIORATION FLAGS AND SUMMARY MEASURES
# ============================================================

# ------------------------------------------------------------
# Define deterioration direction
# ------------------------------------------------------------

# For profitability, liquidity, interest coverage and cash-flow
# ratios, lower values indicate weaker financial fundamentals.
lower_is_worse = [
    "ebitda_margin_w",
    "ebit_margin_w",
    "roa_w",
    "current_ratio_w",
    "interest_coverage_w",
    "ocf_debt_w"
]

# For leverage ratios, higher values indicate weaker fundamentals.
higher_is_worse = [
    "debt_assets_w",
    "debt_equity_w",
    "debt_ebitda_w"
]


# ------------------------------------------------------------
# Construct deterioration flags
# ------------------------------------------------------------

# A deterioration signal requires BOTH:
#
# 1. deterioration relative to the preceding consecutive year; and
# 2. weaker performance than the industry-year peer median.
#
# If either comparison cannot be evaluated, the flag remains missing
# rather than being treated as False.

flag_data = {}


# Lower-is-worse ratios:
# YoY change < 0 AND peer gap < 0
for ratio in lower_is_worse:
    yoy_change = analysis_df[ratio + "_yoy_change"]
    peer_gap = analysis_df[ratio + "_peer_gap"]

    valid = yoy_change.notna() & peer_gap.notna()

    flag = pd.Series(
        pd.NA,
        index=analysis_df.index,
        dtype="boolean"
    )

    flag.loc[valid] = (
        (yoy_change.loc[valid] < 0) &
        (peer_gap.loc[valid] < 0)
    )

    flag_data[ratio + "_deterioration_flag"] = flag


# Higher-is-worse ratios:
# YoY change > 0 AND peer gap > 0
for ratio in higher_is_worse:
    yoy_change = analysis_df[ratio + "_yoy_change"]
    peer_gap = analysis_df[ratio + "_peer_gap"]

    valid = yoy_change.notna() & peer_gap.notna()

    flag = pd.Series(
        pd.NA,
        index=analysis_df.index,
        dtype="boolean"
    )

    flag.loc[valid] = (
        (yoy_change.loc[valid] > 0) &
        (peer_gap.loc[valid] > 0)
    )

    flag_data[ratio + "_deterioration_flag"] = flag


# Add all deterioration flags to the main dataset.
flag_df = pd.DataFrame(flag_data, index=analysis_df.index)

analysis_df = pd.concat(
    [analysis_df, flag_df],
    axis=1
)

deterioration_flags = list(flag_data.keys())


# ------------------------------------------------------------
# Deterioration score and rate
# ------------------------------------------------------------

# Number of ratios that can actually be evaluated.
analysis_df["valid_deterioration_tests"] = (
    analysis_df[deterioration_flags]
    .notna()
    .sum(axis=1)
)

# Number of evaluable ratios that meet the deterioration criteria.
analysis_df["deterioration_score"] = (
    analysis_df[deterioration_flags]
    .astype("Int64")
    .sum(axis=1, min_count=1)
)

# Proportion of valid tests that are deterioration signals.
analysis_df["deterioration_rate"] = (
    analysis_df["deterioration_score"] /
    analysis_df["valid_deterioration_tests"]
).where(
    analysis_df["valid_deterioration_tests"] > 0
)


# ------------------------------------------------------------
# Fundamental warning summary
# ------------------------------------------------------------

# The individual warning indicators were created in Section 2:
# negative_ebitda, negative_equity and negative_ocf.
#
# These are current-level warnings rather than deterioration measures,
# so they remain separate from the deterioration score.

fundamental_flags = [
    "negative_ebitda",
    "negative_equity",
    "negative_ocf"
]

analysis_df["valid_fundamental_tests"] = (
    analysis_df[fundamental_flags]
    .notna()
    .sum(axis=1)
)

analysis_df["fundamental_warning_count"] = (
    analysis_df[fundamental_flags]
    .astype("Int64")
    .sum(axis=1, min_count=1)
)


# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------

print("\nValid deterioration tests:")
print(
    analysis_df["valid_deterioration_tests"]
    .value_counts()
    .sort_index()
)

print("\nDeterioration scores:")
print(
    analysis_df["deterioration_score"]
    .value_counts(dropna=False)
    .sort_index()
)

print("\nDeterioration rate summary:")
print(
    analysis_df["deterioration_rate"]
    .describe()
)

print("\nFundamental warning counts:")
print(
    analysis_df["fundamental_warning_count"]
    .value_counts(dropna=False)
    .sort_index()
)



# ============================================================
# 5. PERSISTENT DETERIORATION
# ============================================================

analysis_df = (
    analysis_df
    .sort_values(["gvkey", "fyear"])
    .copy()
)


# ------------------------------------------------------------
# Define evaluable and high-deterioration company-years
# ------------------------------------------------------------

# A company-year is considered evaluable when at least
# six of the nine deterioration indicators can be assessed.
analysis_df["evaluable_year"] = (
    analysis_df["valid_deterioration_tests"] >= 6
)


# High deterioration = at least 50% of valid indicators
# simultaneously deteriorated over time and were weaker than peers.
#
# Non-evaluable company-years remain missing rather than being
# classified as low deterioration.
analysis_df["high_deterioration_year"] = pd.Series(
    pd.NA,
    index=analysis_df.index,
    dtype="boolean"
)

valid_year = analysis_df["evaluable_year"]

analysis_df.loc[
    valid_year,
    "high_deterioration_year"
] = (
    analysis_df.loc[
        valid_year,
        "deterioration_rate"
    ] >= 0.50
)


# ------------------------------------------------------------
# Identify three-year consecutive windows
# ------------------------------------------------------------

analysis_df["year_minus_1"] = (
    analysis_df.groupby("gvkey")["fyear"].shift(1)
)

analysis_df["year_minus_2"] = (
    analysis_df.groupby("gvkey")["fyear"].shift(2)
)

analysis_df["consecutive_3yr_window"] = (
    (
        analysis_df["fyear"] -
        analysis_df["year_minus_1"] == 1
    ) &
    (
        analysis_df["year_minus_1"] -
        analysis_df["year_minus_2"] == 1
    )
)


# ------------------------------------------------------------
# Persistent deterioration
# ------------------------------------------------------------

# Count high-deterioration years within each rolling
# three-year company window.
#
# A valid persistence assessment requires three consecutive
# fiscal years with evaluable high-deterioration classifications.

high_numeric = (
    analysis_df["high_deterioration_year"]
    .astype("Int64")
)

analysis_df["high_deterioration_3yr_count"] = (
    high_numeric
    .groupby(analysis_df["gvkey"])
    .rolling(3, min_periods=3)
    .sum()
    .reset_index(level=0, drop=True)
)

# Remove rolling results where the three observations
# are not consecutive fiscal years.
analysis_df.loc[
    ~analysis_df["consecutive_3yr_window"],
    "high_deterioration_3yr_count"
] = pd.NA


analysis_df["persistent_deterioration"] = pd.Series(
    pd.NA,
    index=analysis_df.index,
    dtype="boolean"
)

valid_3yr_window = (
    analysis_df["high_deterioration_3yr_count"].notna()
)

analysis_df.loc[
    valid_3yr_window,
    "persistent_deterioration"
] = (
    analysis_df.loc[
        valid_3yr_window,
        "high_deterioration_3yr_count"
    ] >= 2
)


# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------

print("\nEvaluable company-years:")
print(
    analysis_df["evaluable_year"]
    .value_counts(dropna=False)
)

print("\nHigh-deterioration years:")
print(
    analysis_df["high_deterioration_year"]
    .value_counts(dropna=False)
)

print("\nPersistent deterioration:")
print(
    analysis_df["persistent_deterioration"]
    .value_counts(dropna=False)
)



# ============================================================
# 6. 2024 SCREENING AND CASE-COMPANY SELECTION
# ============================================================

# ------------------------------------------------------------
# Construct the 2024 screening sample
# ------------------------------------------------------------

# Restrict the current-year screen to evaluable company-years.
latest = analysis_df[
    (analysis_df["fyear"] == 2024) &
    (analysis_df["evaluable_year"])
].copy()

print("\n2024 evaluable companies:")
print(len(latest))


# ------------------------------------------------------------
# Current peer-weakness indicators
# ------------------------------------------------------------

# Peer weakness measures whether the company's current ratio
# is weaker than its industry-year median, regardless of whether
# the ratio deteriorated relative to the previous year.

peer_weakness = {}


# Lower-is-worse ratios:
# company value below peer median = peer weakness.
for ratio in lower_is_worse:
    peer_gap = latest[ratio + "_peer_gap"]

    flag = pd.Series(
        pd.NA,
        index=latest.index,
        dtype="boolean"
    )

    valid = peer_gap.notna()

    flag.loc[valid] = (
        peer_gap.loc[valid] < 0
    )

    peer_weakness[
        ratio + "_peer_weakness"
    ] = flag


# Higher-is-worse ratios:
# company value above peer median = peer weakness.
for ratio in higher_is_worse:
    peer_gap = latest[ratio + "_peer_gap"]

    flag = pd.Series(
        pd.NA,
        index=latest.index,
        dtype="boolean"
    )

    valid = peer_gap.notna()

    flag.loc[valid] = (
        peer_gap.loc[valid] > 0
    )

    peer_weakness[
        ratio + "_peer_weakness"
    ] = flag


peer_df = pd.DataFrame(
    peer_weakness,
    index=latest.index
)

latest = pd.concat(
    [latest, peer_df],
    axis=1
)

peer_flags = list(peer_weakness.keys())


# ------------------------------------------------------------
# Peer-weakness score and rate
# ------------------------------------------------------------

latest["valid_peer_tests"] = (
    latest[peer_flags]
    .notna()
    .sum(axis=1)
)

latest["peer_weakness_count"] = (
    latest[peer_flags]
    .astype("Int64")
    .sum(axis=1, min_count=1)
)

latest["peer_weakness_rate"] = (
    latest["peer_weakness_count"] /
    latest["valid_peer_tests"]
).where(
    latest["valid_peer_tests"] > 0
)


print("\nValid peer tests:")
print(
    latest["valid_peer_tests"]
    .value_counts()
    .sort_index()
)

print("\nPeer-weakness rate summary:")
print(
    latest["peer_weakness_rate"]
    .describe()
)

print("\n2024 persistence:")
print(
    latest["persistent_deterioration"]
    .value_counts(dropna=False)
)


# ------------------------------------------------------------
# Initial candidate screen
# ------------------------------------------------------------

# Candidate firms must:
#
# 1. have at least six valid peer comparisons;
# 2. show deterioration in at least 50% of valid indicators; and
# 3. currently be weaker than peers in at least 50% of
#    valid indicators.

candidates = latest[
    (latest["valid_peer_tests"] >= 6) &
    (latest["deterioration_rate"] >= 0.50) &
    (latest["peer_weakness_rate"] >= 0.50)
].copy()

print("\nInitial candidate companies:")
print(len(candidates))


# Rank candidates for diagnostic inspection.
candidates = candidates.sort_values(
    [
        "persistent_deterioration",
        "deterioration_rate",
        "peer_weakness_rate",
        "fundamental_warning_count"
    ],
    ascending=[False, False, False, False],
    na_position="last"
)

print("\nHighest-ranked initial candidates:")
print(
    candidates[
        [
            "gvkey",
            "tic",
            "conm",
            "naics3",
            "deterioration_score",
            "valid_deterioration_tests",
            "deterioration_rate",
            "peer_weakness_count",
            "valid_peer_tests",
            "peer_weakness_rate",
            "persistent_deterioration",
            "fundamental_warning_count"
        ]
    ]
    .head(30)
    .to_string(index=False)
)


# ------------------------------------------------------------
# Historical coverage
# ------------------------------------------------------------

history = (
    analysis_df
    .groupby("gvkey")
    .agg(
        years_in_sample=("fyear", "nunique"),
        first_year=("fyear", "min"),
        last_year=("fyear", "max"),
        evaluable_years=("evaluable_year", "sum")
    )
    .reset_index()
)

candidates = candidates.merge(
    history,
    on="gvkey",
    how="left"
)


# ------------------------------------------------------------
# Strong case-study pool
# ------------------------------------------------------------

# Require persistent deterioration, strong current data
# completeness and sufficient historical coverage.

case_pool = candidates[
    candidates["persistent_deterioration"].fillna(False) &
    (candidates["valid_deterioration_tests"] >= 8) &
    (candidates["valid_peer_tests"] >= 8) &
    (candidates["years_in_sample"] >= 8) &
    (candidates["evaluable_years"] >= 5)
].copy()

print("\nStrong case-study pool:")
print(len(case_pool))


case_pool = case_pool.sort_values(
    [
        "deterioration_rate",
        "peer_weakness_rate",
        "fundamental_warning_count",
        "years_in_sample"
    ],
    ascending=[False, False, False, False],
    na_position="last"
)

print("\nHighest-ranked strong case-study candidates:")
print(
    case_pool[
        [
            "gvkey",
            "tic",
            "conm",
            "naics3",
            "deterioration_score",
            "valid_deterioration_tests",
            "deterioration_rate",
            "peer_weakness_count",
            "valid_peer_tests",
            "peer_weakness_rate",
            "fundamental_warning_count",
            "years_in_sample",
            "evaluable_years"
        ]
    ]
    .head(40)
    .to_string(index=False)
)


# ------------------------------------------------------------
# Final case-company selection
# ------------------------------------------------------------

# Six companies were selected from the strong case-study pool
# to provide examples from different industries.

selected_tickers = [
    "XRX",
    "DBI",
    "AAOI",
    "WTI",
    "CLF",
    "NDLS"
]

selected_2024 = case_pool[
    case_pool["tic"].isin(selected_tickers)
].copy()

print("\nSelected 2024 case companies:")
print(
    selected_2024[
        [
            "tic",
            "conm",
            "naics3",
            "deterioration_score",
            "valid_deterioration_tests",
            "deterioration_rate",
            "peer_weakness_count",
            "valid_peer_tests",
            "peer_weakness_rate",
            "persistent_deterioration",
            "fundamental_warning_count",
            "years_in_sample",
            "evaluable_years"
        ]
    ]
    .sort_values("tic")
    .to_string(index=False)
)


# ------------------------------------------------------------
# Extract complete histories for Tableau
# ------------------------------------------------------------

selected_gvkeys = selected_2024["gvkey"].unique()

selected_history = analysis_df[
    analysis_df["gvkey"].isin(selected_gvkeys)
].copy()

selected_history = (
    selected_history
    .sort_values(["tic", "fyear"])
)

print("\nSelected-company history:")
print(
    selected_history[
        ["tic", "conm", "fyear"]
    ]
    .to_string(index=False)
)

print(
    "\nSelected-company observations:",
    len(selected_history)
)


# ------------------------------------------------------------
# Export final local Tableau datasets
# ------------------------------------------------------------

# These derived Compustat datasets are generated locally and
# should not be distributed through the public repository.

OUTPUT_DIR = Path("data_output")
OUTPUT_DIR.mkdir(exist_ok=True)

selected_2024.to_csv(
    OUTPUT_DIR / "selected_companies_2024.csv",
    index=False
)

selected_history.to_csv(
    OUTPUT_DIR / "selected_companies_history.csv",
    index=False
)

print("\nFinal local Tableau datasets saved.")
