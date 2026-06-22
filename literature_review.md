 # Literature Review: Hurricane Mobility Disruption and Recovery Dynamics

## 1. Mobile Phone Data for Disaster Research

The emergence of large-scale mobile phone location data has transformed disaster research by enabling observation of human mobility at unprecedented spatiotemporal resolution. Yabe et al. (2022) provide a comprehensive review of mobile phone location data applications for disasters, noting that GPS signals from smartphones can provide location information for millions of samples at high frequency (approximately 50 data points per day) with spatial granularity of roughly 100 meters, across longitudinal timeframes spanning months before and after disaster events (Yabe et al., 2022, *Computers, Environment and Urban Systems*).

SafeGraph point-of-interest (POI) visitation data have been widely adopted in disaster mobility research. Researchers have used SafeGraph data to track visits to hospitals, gas stations, stores, and other establishments before and during hurricanes, enabling measurement of functional disruption and recovery at fine geographic scales (Texas A&M TEES, 2021). Podesta et al. (2021) used SafeGraph POI visit data to develop fluctuation-based resilience metrics for Hurricane Harvey, quantifying community resilience through deviations in visit patterns (*Journal of the Royal Society Interface*, 18, 20210158). Yuan et al. (2021) combined SafeGraph mobility data with credit card transactions to assess disaster impacts and recovery patterns after Hurricane Harvey (*Computers, Environment and Urban Systems*, 84, 101545). The bias characteristics of SafeGraph data across spatial scales have been systematically examined, with studies noting the importance of understanding representativeness when drawing conclusions about population-level mobility behavior (Kang et al., 2024, *PLOS ONE*).

## 2. Hurricane Impacts on Human Mobility

### 2.1 Mobility Disruption Patterns

Recent studies have quantified hurricane-induced mobility disruptions using digital trace data. Research on Hurricane Ian in southwest Florida revealed steep declines in POI visitation across urban, suburban, and rural counties, with particularly acute disruptions in urban centers and uneven recovery patterns across different area types (Li et al., 2025, *Transportation Research Part D*). A multiscale analysis of Hurricane Ian's impact on Florida's mobility networks demonstrated substantial decreases in connectivity and efficiency during the hurricane, though networks showed resilience through swift post-hurricane recovery (Chen et al., 2024, *Transportation Research Part D*).

Category-specific disruption patterns vary markedly. During Hurricane Ida, analysis revealed that healthcare visitation increased by 50% during disruption periods, while food businesses experienced an 18.7% decrease and religious institutions saw a 22.4% decline (Villanova University, 2023). These differential impacts across activity types highlight the importance of disaggregating mobility into functional categories rather than treating it as a single aggregate measure.

### 2.2 Hurricanes Helene and Milton (2024)

Directly relevant to the present study, a recent analysis examined adaptive mobility responses during Hurricanes Helene and Milton using 3.56 billion high-resolution foot-traffic records from mobile devices within 50 miles of the storm tracks, representing the mobility of 24.4 million residents (published in *Environmental Research Letters*). The study found marked differences in evacuation behavior between the two hurricanes: Milton led to a significant 29% rise in out-region movement beginning three days before landfall, while Helene saw only a modest 5% increase in out-of-region movement in the three days before landfall despite emergency declarations and evacuation orders. This disparity was attributed to differences in coastal versus inland geography, socioeconomic resources, and transportation infrastructure access.

## 3. Evacuation Behavior and Socioeconomic Determinants

### 3.1 Disparities in Evacuation

Hong et al. (2021) analyzed mobility patterns of more than 800,000 anonymized mobile devices in Houston during Hurricane Harvey, representing approximately 35% of the local population. Using changes in mobility behavior before, during, and after the disaster, they defined community resilience capacity as a function of impact magnitude and time-to-recovery, finding clear socioeconomic and racial disparities in both resilience capacity and evacuation patterns (*Nature Communications*, 12, 1870).

Deria et al. (2020) used mobile phone data to analyze evacuation and reentry patterns after Hurricane Irma, revealing inequity in post-disaster evacuation destinations across income groups and demonstrating how socioeconomic disparities influenced not only who evacuated but where they evacuated to, when they evacuated, and how long they remained evacuated (*Transportation Research Part D*). Coleman et al. (2020) provided empirical evidence of disparities in mobility recovery from hurricanes, demonstrating that disadvantaged communities experienced systematically slower recovery (*Reliability Engineering & System Safety*, 197, 106805). Esmalian et al. (2022) further used SafeGraph data to show that socially vulnerable populations experienced longer disruptions and slower recovery in mobility after Hurricane Harvey (*International Journal of Disaster Risk Reduction*, 73, 102874).

### 3.2 Context-Dependent Disparities

A comprehensive study investigating income and race disparities across seven hurricane events found that even with a consistent study design, disparities in evacuation among different socioeconomic groups vary on a case-by-case basis (Yabe et al., 2024, *Scientific Reports*). This finding underscores the importance of multi-event comparative designs---such as the present study's comparison of Helene and Milton---to understand the conditions under which socioeconomic factors amplify or attenuate disparities.

### 3.3 Predictors of Evacuation Decisions

Beyond socioeconomic factors, research has identified efficacy beliefs and risk perceptions as important predictors of hurricane evacuation decisions (*npj Natural Hazards*, 2024). Huang et al. (2016) conducted a meta-analysis of 49 hurricane evacuation studies, finding that risk perception, storm characteristics, and social cues were stronger predictors than demographics alone (*Environment and Behavior*, 48(8), 991-1029). Facebook data have also been used to understand evacuation behavior, expanding the range of digital data sources available for studying disaster response (Bao et al., 2024, *International Journal of Disaster Risk Reduction*). Martin et al. (2020) used geotagged tweets to track population movements to and from Puerto Rico after Hurricane Maria, finding that socioeconomic factors predicted who left and who returned (*Population and Environment*, 42, 4-27).

## 4. Social Vulnerability Frameworks

### 4.1 The Social Vulnerability Index

Cutter et al. developed the Social Vulnerability Index (SoVI), consisting of factors derived from Census data that produce composite scores of county-level vulnerability to environmental hazards. The SoVI has been widely adopted in hazard mitigation planning and disaster recovery targeting. Flanagan et al. (2011) developed the CDC's Social Vulnerability Index (SVI), comprising four themes: Socioeconomic Status, Household Composition and Disability, Minority Status and Language, and Housing Type and Transportation (*Journal of Homeland Security and Emergency Management*).

### 4.2 Disaster Resilience of Place (DROP) Model

Cutter et al.'s (2008) DROP model provides a theoretical framework showing how human systems, environmental systems, and the built environment interact to produce antecedent conditions containing both inherent vulnerabilities and inherent resilience. The Baseline Resilience Indicators for Communities (BRIC) methodology, building on DROP, assesses resilience using composite indicators of social, economic, institutional, infrastructure, and community capacities (Cutter et al., 2010).

### 4.3 Vulnerability-Resilience Nexus

Research connecting social vulnerability and community resilience has found a negative correlation: the most vulnerable counties tend to be the least resilient (Cutter et al., 2014, *Global Environmental Change*). Rufat et al. (2019) found that communities with socially vulnerable populations were slow to recover even without heavy physical damage, while vulnerable communities experiencing heavy damage were the slowest to recover (*Sustainability Science*).

## 5. Disaster Recovery Measurement

### 5.1 Mobility-Based Recovery Metrics

Yabe and Ukkusuri have pioneered data-driven approaches to disaster resilience measurement, advocating for dynamical complex systems approaches that leverage large-scale human mobility data to quantify recovery trajectories (Yabe et al., 2022, *PNAS*). Their framework defines resilience through the dual dimensions of impact magnitude and recovery time, measured from deviations in mobility patterns relative to pre-disaster baselines.

Recent work has used Bayesian belief network-based anomaly detection methods applied to location-based services data to identify household-level lack of recovery, as demonstrated for Hurricane Irma (Lee et al., 2025, *Computers, Environment and Urban Systems*). Urban-rural differences in post-disaster recovery have been revealed through spatiotemporal heterogeneity analysis of mobility data (*npj Urban Sustainability*, 2023).

### 5.2 Counterfactual Baseline Approaches

The use of time-series models to construct counterfactual baselines---estimating what mobility would have been absent the hurricane---is methodologically analogous to approaches used in causal inference. Brodersen et al. (2015) developed the CausalImpact framework using Bayesian structural time-series models to estimate causal effects of interventions from time-series data (Google, *Annals of Applied Statistics*). SARIMA-based counterfactual models have been applied to examine the extent of air pollution reduction following state-level emergency declarations during COVID-19 (Granella et al., 2021, *Scientific Reports*), demonstrating the validity of seasonal ARIMA for constructing "what would have happened" scenarios against which to measure disruption.

### 5.3 Theil-Sen Robust Estimation

The Theil-Sen estimator, a nonparametric method defining the slope as the median of all pairwise slopes, offers advantages for recovery trend estimation due to its robustness to outliers---tolerating up to 29.3% corrupted observations without affecting the estimate (Sen, 1968, *Journal of the American Statistical Association*; Theil, 1950). In environmental science, the Theil-Sen estimator has been widely applied for trend detection in water quality data and climate datasets where measurements contain extreme values or censoring (Helsel and Frans, 2006, *Environmental Science & Technology*). Its application to disaster recovery trend estimation, as in the present study, leverages this robustness against the noisy, non-stationary mobility data characteristic of post-disaster periods.

## 6. Spatial Analysis Methods in Disaster Research

### 6.1 Spatial Autocorrelation

Moran's I statistic is widely used to test for spatial autocorrelation in disaster impact variables, determining whether observed values at nearby locations are more similar than expected by chance. When significant spatial autocorrelation is detected in regression residuals, it indicates that standard OLS models may produce biased estimates and that spatial regression approaches are warranted. Studies of hurricane damage have applied both global and local Moran's I to identify spatial clustering of impact severity (Anselin, 1995, *Geographical Analysis*).

### 6.2 Geographically Weighted Regression

GWR, introduced by Brunsdon et al. (1996, *Geographical Analysis*) and further developed by Fotheringham et al. (2002), constructs separate OLS equations for each observation incorporating nearby data points within a bandwidth, allowing regression coefficients to vary spatially. Evidence of non-stationarity is indicated when the AICc for GWR is smaller than for the global model. A recent study of Texas hurricane risk achieved an adjusted R-squared of 0.95 using GWR, revealing spatial non-stationarity in the relationships between vulnerability indicators and risk distribution (2025, *Journal of Geovisualization and Spatial Analysis*). Comber et al. (2023) provide a comprehensive route map for successful GWR applications (*Geographical Analysis*).

### 6.3 Mixed-Effects Models for Multi-Event Comparison

Hierarchical or mixed-effects models enable pooling of data across multiple disaster events while accounting for event-level heterogeneity through random effects. This approach has been applied in disaster contexts using mixed logit models with random parameters to identify factors affecting individual recovery decisions across hurricane events (Tobin & Montz, *International Journal of Disaster Risk Reduction*). The random intercept structure allows estimation of common socioeconomic predictor effects while capturing baseline differences between events---in the present study, between Category 4 (Helene) and Category 5 (Milton) hurricanes.

## 7. Flow Decomposition and Network Approaches

The decomposition of mobility into within-region, inflow, and outflow components builds on transportation network analysis frameworks. Studies have analyzed how mobility networks fragment during disasters, with within-region flows reflecting local activity resumption, inflows capturing external aid and resource delivery, and outflows measuring evacuation dynamics (Yabe et al., 2019, *Applied Network Science*). Pre-disaster inter-city social ties have been shown to predict post-disaster recovery flows, as demonstrated for Hurricane Maria where cities with stronger pre-existing social connections received more recovery-supporting inflows (Yabe et al., 2019).

## 8. Research Gaps and Contributions

Several gaps in the existing literature motivate the present study:

1. **Category-specific mobility disaggregation**: Most studies analyze aggregate mobility or focus on a single activity type. Few have systematically compared disruption and recovery across multiple functional categories (transportation, healthcare, education, retail, government, utilities) within a unified framework.

2. **Multi-hurricane comparative design with consistent methodology**: While studies have compared evacuation rates across events, few apply identical analytical pipelines (same baseline model, same recovery metrics) to multiple hurricanes to isolate the effect of storm intensity and geographic context.

3. **Flow-type decomposition at local scales**: The separation of within-region, inflow, and outflow dynamics at the county level, combined with recovery trend estimation, extends beyond the regional-aggregate analyses that dominate the literature.

4. **Robust recovery estimation**: The application of Theil-Sen slope estimation to mobility recovery curves is novel; most studies use simpler threshold-based recovery definitions (e.g., return to 90% of baseline) that are sensitive to daily fluctuations.

5. **Spatial diagnostics before model selection**: The systematic use of LOWESS visualization, Moran's I testing, and residual mapping to determine whether nonlinearities are spatial in nature---before choosing between GAM and GWR---represents a methodologically rigorous diagnostic approach.

6. **Hurricanes Helene and Milton**: As recent 2024 events, there is limited peer-reviewed literature on their mobility impacts, making the present study among the first comprehensive analyses of category-specific disruption and recovery for these storms.

---

## References

> **Note**: All references should be verified against Google Scholar or the original publication before submission. Some volume/issue/page numbers may require correction.

Anselin, L. (1995). Local indicators of spatial association---LISA. *Geographical Analysis*, 27(2), 93-115.

Bao, Y., et al. (2024). Understanding hurricane evacuation behavior from Facebook data. *International Journal of Disaster Risk Reduction*.

Brodersen, K. H., et al. (2015). Inferring causal impact using Bayesian structural time-series models. *Annals of Applied Statistics*, 9(1), 247-274.

Brunsdon, C., Fotheringham, A. S., & Charlton, M. (1996). Geographically weighted regression: A method for exploring spatial nonstationarity. *Geographical Analysis*, 28(4), 281-298.

Coleman, N., Esmalian, A., & Mostafavi, A. (2020). Equitable resilience in infrastructure systems: Empirical evidence of disparities in mobility recovery from hurricanes. *Reliability Engineering & System Safety*, 197, 106805.

Chen, Z., et al. (2024). Unraveling Hurricane Ian's impact: A multiscale analysis of mobility networks in Florida. *Transportation Research Part D*.

Comber, A., et al. (2023). A route map for successful applications of geographically weighted regression. *Geographical Analysis*.

Cutter, S. L., Barnes, L., Berry, M., et al. (2008). A place-based model for understanding community resilience to natural disasters. *Global Environmental Change*, 18(4), 598-606.

Cutter, S. L., Ash, K. D., & Emrich, C. T. (2014). The geographies of community disaster resilience. *Global Environmental Change*, 29, 65-77.

Cutter, S. L., Burton, C. G., & Emrich, C. T. (2010). Disaster resilience indicators for benchmarking baseline conditions. *Journal of Homeland Security and Emergency Management*, 7(1).

Deria, A., et al. (2020). Effects of income inequality on evacuation, reentry and segregation after disasters. *Transportation Research Part D*.

Esmalian, A., Yuan, F., Coleman, N., & Mostafavi, A. (2022). Evaluating the disparate impacts of Hurricane Harvey on socially vulnerable populations using mobility data. *International Journal of Disaster Risk Reduction*, 73, 102874.

Flanagan, B. E., et al. (2011). A social vulnerability index for disaster management. *Journal of Homeland Security and Emergency Management*, 8(1).

Fotheringham, A. S., Brunsdon, C., & Charlton, M. (2002). *Geographically Weighted Regression: The Analysis of Spatially Varying Relationships*. John Wiley & Sons.

Granella, F., et al. (2021). Counterfactual time series analysis of short-term change in air pollution following the COVID-19 state of emergency in the United States. *Scientific Reports*, 11, 23211.

Helsel, D. R., & Frans, L. M. (2006). Regional Kendall test for trend. *Environmental Science & Technology*, 40(13), 4066-4073.

Huang, S. K., Lindell, M. K., & Prater, C. S. (2016). Who leaves and who stays? A review and statistical meta-analysis of hurricane evacuation studies. *Environment and Behavior*, 48(8), 991-1029.

Hong, B., Bonczak, B. J., Gupta, A., et al. (2021). Measuring inequality in community resilience to natural disasters using large-scale mobility data. *Nature Communications*, 12, 1870.

Kang, Y., et al. (2024). Understanding the bias of mobile location data across spatial scales and over time: A comprehensive analysis of SafeGraph data in the United States. *PLOS ONE*.

Lee, S., et al. (2025). Using mobile phone data for quantifying large-scale household-level disaster recovery. *Computers, Environment and Urban Systems*.

Li, Y., et al. (2025). Mobility disruption and recovery in southwest Florida's elderly-dense communities during Hurricane Ian. *Transportation Research Part D*.

Martin, Y., Cutter, S. L., Li, Z., Emrich, C. T., & Mitchell, J. T. (2020). Using geotagged tweets to track population movements to and from Puerto Rico after Hurricane Maria. *Population and Environment*, 42, 4-27.

Podesta, C., Coleman, N., Esmalian, A., Yuan, F., & Mostafavi, A. (2021). Quantifying community resilience based on fluctuations in visits to points-of-interest derived from digital trace data. *Journal of the Royal Society Interface*, 18(177), 20210158.

Rufat, S., et al. (2019). How valid are social vulnerability models? *Annals of the American Association of Geographers*, 109(4), 1131-1153.

Sen, P. K. (1968). Estimates of the regression coefficient based on Kendall's tau. *Journal of the American Statistical Association*, 63(324), 1379-1389.

Theil, H. (1950). A rank-invariant method of linear and polynomial regression analysis. *Indagationes Mathematicae*, 12(85), 173.

Yabe, T., Rao, P. S. C., Ukkusuri, S. V., & Cutter, S. L. (2022). Toward data-driven, dynamical complex systems approaches to disaster resilience. *Proceedings of the National Academy of Sciences*, 119(8), e2111997119.

Yabe, T., Tsubouchi, K., Fujiwara, N., et al. (2019). Mobile phone data reveals the importance of pre-disaster inter-city social ties for recovery after Hurricane Maria. *Applied Network Science*, 4(1), 98.

Yabe, T., Ukkusuri, S. V., et al. (2022). Mobile phone location data for disasters: A review from natural hazards and epidemics. *Computers, Environment and Urban Systems*, 93, 101747.

Yabe, T., et al. (2024). Understanding of income and race disparities in hurricane evacuation is contingent upon study case and design. *Scientific Reports*, 14, 28643.

Yuan, F., Esmalian, A., & Mostafavi, A. (2021). Unveiling spatial patterns of disaster impacts and recovery using credit card transaction variances. *Computers, Environment and Urban Systems*, 84, 101545.

[Adaptive mobility responses during Hurricanes Helene and Milton in 2024]. *Environmental Research Letters* (2025). PMC12236882.
