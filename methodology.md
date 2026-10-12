## Methodology

The project aims to identify U.S. non-financial companies showing deterioration in credit-relevant financial fundamentals over time and relative to industry peers. 

It is designed as a financial-fundamentals screening exercise rather than a credit rating, probability-of-default model or lending recommendation.

### Data and Sample Construction

The analysis uses **WRDS Compustat Fundamentals Annual data from 2010 to 2024**. The raw dataset was filtered to retain U.S.-incorporated firms reporting in USD using standardized, consolidated industrial-format financial statements. Finance and insurance companies were excluded because their balance-sheet structures and leverage measures are not directly comparable with those of non-financial corporations. Where more than one observation existed for the same company and fiscal year, the observation with the latest reporting date was retained.

The resulting analytical sample contained 78,325 company-year observations.

### Financial Ratios

The analysis focuses on profitability, liquidity, leverage, debt-servicing capacity and operating cash-flow strength. Nine credit-relevant financial ratios were constructed:

1. **EBITDA Margin = EBITDA / Sales**  
   Measures operating profitability before depreciation, amortization, interest and taxes. Persistent declines may indicate weakening underlying operating performance.

2. **EBIT Margin = EBIT / Sales**  
   Measures operating profitability after depreciation and amortization but before interest and taxes.

3. **Return on Assets (ROA) = Net Income / Total Assets**  
   Measures how effectively the company generates earnings from its asset base.

4. **Current Ratio = Current Assets / Current Liabilities**  
   Measures short-term liquidity and the company's ability to cover short-term obligations with short-term assets.

5. **Debt / Assets = Total Debt / Total Assets**  
   Measures the proportion of the asset base financed through debt.

6. **Debt / Equity = Total Debt / Common Equity**  
   Measures financial leverage relative to shareholders' equity. The ratio was calculated only when common equity was positive. Negative equity makes the ratio economically difficult to interpret, while extreme ratios resulting from very small positive equity were addressed through winsorization.

7. **Debt / EBITDA = Total Debt / EBITDA**  
   Relates the debt burden to operating earnings capacity. Higher values generally indicate greater leverage. The ratio was calculated only when EBITDA was positive.

8. **Interest Coverage = EBIT / Interest Expense**  
   Measures the company's ability to cover interest costs from operating earnings. Lower or negative values indicate weaker debt-servicing capacity.

9. **Operating Cash Flow / Debt = Operating Cash Flow / Total Debt**  
   Measures cash-generation capacity relative to debt and complements earnings-based measures because debt ultimately has to be serviced with cash.

For debt-based ratios, Total Debt was defined as short-term debt plus long-term debt.

### Missing Data and Ratio Treatment

Missing observations were handled ratio by ratio rather than deleting every company-year with an incomplete financial statement. Ratios were calculated only when the relevant denominator was positive, avoiding undefined or economically difficult-to-interpret ratio values. For example, Debt / EBITDA was not calculated for non-positive EBITDA, while Debt / Equity was not calculated for non-positive common equity. Negative profitability and cash-flow numerators were retained because they contain economically relevant information.

### Winsorization

Because raw financial ratios contained extreme values, the original ratios were retained while separate analytical versions were winsorized at the 1st and 99th percentiles within each fiscal year. These winsorized ratios were used for year-over-year deterioration tests, peer comparisons and visualization so that a small number of extreme observations would not dominate the analysis.

### Industry Peer Benchmarks

Peer benchmarks were constructed using the median ratio of firms in the same three-digit NAICS industry and fiscal year. A peer benchmark was used only when at least 20 valid observations were available for that ratio within the industry-year group. The median was preferred to the mean because several financial ratios exhibited highly skewed distributions.

### Deterioration Framework

For each ratio, two perspectives were combined when assessing financial deterioration:

- **Time-series comparison:** whether a company's financial ratio deteriorated relative to its preceding consecutive fiscal year.
- **Peer comparison:** whether the company's financial ratio was weaker than the median of firms in the same three-digit NAICS industry and fiscal year.

A deterioration signal was recorded only when both conditions were met.

For profitability, liquidity, interest coverage and cash-flow ratios, a decline was treated as deterioration. For leverage ratios, an increase was treated as deterioration.

A **deterioration score** counted the number of ratios flagged as deterioration signals. The **deterioration rate** divided the number of deterioration signals by the number of ratios that could actually be evaluated for that company-year *(Deterioration Rate = Number of deterioration signals / Number of valid deterioration tests)*.

This distinction prevents missing information from being treated as evidence of financial strength.

Company-years with at least six valid deterioration tests were considered evaluable. A deterioration rate of at least 50% was classified as a high-deterioration year. The 50% threshold is a project-specific screening rule rather than an established credit-rating or default-prediction threshold.

### Persistence and Fundamental Warnings

Three additional fundamental warnings were tracked separately:

- negative EBITDA
- negative common equity
- negative operating cash flow

These warnings were not added directly to the deterioration score in order to avoid double-counting related financial weaknesses.

Persistent deterioration was identified using rolling three-year windows. A company was classified as showing persistent deterioration when at least two of three consecutive fiscal years were classified as high-deterioration years.

### Peer Weakness Construction

A separate measure of peer weakness was also constructed for the latest fiscal year. A ratio was classified as weak relative to peers when it was below the industry-year median for profitability, liquidity, interest coverage or cash-flow measures, or above the industry-year median for leverage measures. The **peer-weakness rate** represented the proportion of valid ratios classified as weaker than peers.

### Company Selection

The full analytical sample was screened before any case companies were selected.

For the 2024 screening stage, only company-years with at least six valid deterioration tests were considered evaluable. An initial candidate screen required:

- a deterioration rate of at least 50%;
- a peer-weakness rate of at least 50%; and
- at least six valid peer-comparison tests.

A stronger case-study pool was then identified using additional requirements:

- persistent deterioration;
- at least eight valid deterioration tests in 2024;
- at least eight valid peer-comparison tests in 2024;
- at least eight years of observations in the sample; and
- at least five evaluable years.

This produced a pool of firms satisfying the required persistence, current-year deterioration, peer-weakness and data-availability criteria. From this pool, six companies from different industries were selected for presentation:

- Xerox Holdings Corporation (XRX)
- Designer Brands Inc. (DBI)
- Applied Optoelectronics Inc. (AAOI)
- W&T Offshore Inc. (WTI)
- Cleveland-Cliffs Inc. (CLF)
- Noodles & Company (NDLS)

The six selected companies contributed 88 company-year observations in total to the final case-study dashboard. All six exhibited persistent deterioration, high 2024 deterioration and peer-weakness rates, and sufficiently complete historical observations. Selecting companies from different industries also provides variation across the case studies rather than concentrating the presentation within a single sector.

### Interpretation and Limitations

The resulting framework should be interpreted as a corporate credit-monitoring and screening tool. It identifies firms whose profitability, liquidity, leverage, debt-servicing capacity and cash-flow fundamentals warrant closer investigation. It does not constitute a credit rating, probability-of-default estimate or lending recommendation.
