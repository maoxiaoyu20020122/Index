# 成分股穿透因子轮动结果

- 数据：20140101 至 20260902
- 绩效统计：20160101 至 20260902
- 目标：未来 20 日收益
- 规则：滚动窗口内按 ICIR、方向胜率、收益贡献筛选因子；仅保留胜率不低于 50% 的因子；按质量分数加权。

## 策略表现前二十
|   ann_ret |   ann_vol |   sharpe |   max_drawdown |   win_rate |   n_days | index   | strategy                      | mode         |   window |   top_n |   benchmark_ann_ret |   benchmark_sharpe |   benchmark_max_drawdown |
|----------:|----------:|---------:|---------------:|-----------:|---------:|:--------|:------------------------------|:-------------|---------:|--------:|--------------------:|-------------------:|-------------------------:|
|    0.0963 |    0.1335 |   0.7211 |        -0.1770 |     0.2154 |     2591 | CSI500  | factor_rotation_h20_w504_top8 | weekly_hold  |      504 |       8 |              0.0030 |             0.0132 |                  -0.4313 |
|    0.0892 |    0.1498 |   0.5954 |        -0.2349 |     0.2269 |     2591 | CSI1000 | factor_rotation_h20_w504_top4 | weekly_hold  |      504 |       4 |             -0.0308 |            -0.1223 |                  -0.5726 |
|    0.1085 |    0.1858 |   0.5839 |        -0.2466 |     0.1330 |     1616 | STAR50  | factor_rotation_h20_w504_top8 | monthly_hold |      504 |       8 |              0.0810 |             0.2379 |                  -0.6266 |
|    0.0878 |    0.1518 |   0.5787 |        -0.2538 |     0.2293 |     2591 | CSI1000 | factor_rotation_h20_w504_top8 | weekly_hold  |      504 |       8 |             -0.0308 |            -0.1223 |                  -0.5726 |
|    0.0804 |    0.1457 |   0.5516 |        -0.1994 |     0.2208 |     2591 | CSI1000 | factor_rotation_h20_w504_top6 | weekly_hold  |      504 |       6 |             -0.0308 |            -0.1223 |                  -0.5726 |
|    0.0747 |    0.1463 |   0.5105 |        -0.2267 |     0.1250 |     1616 | STAR50  | factor_rotation_h20_w504_top6 | weekly_hold  |      504 |       6 |              0.0810 |             0.2379 |                  -0.6266 |
|    0.0898 |    0.1759 |   0.5104 |        -0.1973 |     0.1361 |     1616 | STAR50  | factor_rotation_h20_w504_top4 | monthly_hold |      504 |       4 |              0.0810 |             0.2379 |                  -0.6266 |
|    0.0950 |    0.1892 |   0.5019 |        -0.2625 |     0.1392 |     1616 | STAR50  | factor_rotation_h20_w504_top4 | weekly_hold  |      504 |       4 |              0.0810 |             0.2379 |                  -0.6266 |
|    0.0964 |    0.1954 |   0.4931 |        -0.2373 |     0.1702 |     1616 | STAR50  | factor_rotation_h20_w252_top4 | weekly_hold  |      252 |       4 |              0.0810 |             0.2379 |                  -0.6266 |
|    0.0719 |    0.1505 |   0.4781 |        -0.2704 |     0.2339 |     2591 | CSI500  | factor_rotation_h20_w126_top6 | monthly_hold |      126 |       6 |              0.0030 |             0.0132 |                  -0.4313 |
|    0.0593 |    0.1492 |   0.3975 |        -0.3067 |     0.2300 |     2591 | CSI500  | factor_rotation_h20_w126_top6 | weekly_hold  |      126 |       6 |              0.0030 |             0.0132 |                  -0.4313 |
|    0.0543 |    0.1419 |   0.3824 |        -0.2588 |     0.2165 |     2591 | CSI500  | factor_rotation_h20_w504_top8 | monthly_hold |      504 |       8 |              0.0030 |             0.0132 |                  -0.4313 |
|    0.0651 |    0.1906 |   0.3417 |        -0.3484 |     0.1677 |     1616 | STAR50  | factor_rotation_h20_w252_top8 | weekly_hold  |      252 |       8 |              0.0810 |             0.2379 |                  -0.6266 |
|    0.0455 |    0.1474 |   0.3088 |        -0.5114 |     0.2459 |     2591 | CSI500  | factor_rotation_h20_w252_top6 | weekly_hold  |      252 |       6 |              0.0030 |             0.0132 |                  -0.4313 |
|    0.0582 |    0.1890 |   0.3076 |        -0.2223 |     0.1219 |     1616 | STAR50  | factor_rotation_h20_w504_top8 | weekly_hold  |      504 |       8 |              0.0810 |             0.2379 |                  -0.6266 |
|    0.0493 |    0.1675 |   0.2941 |        -0.3167 |     0.1726 |     1616 | STAR50  | factor_rotation_h20_w126_top6 | monthly_hold |      126 |       6 |              0.0810 |             0.2379 |                  -0.6266 |
|    0.0454 |    0.1545 |   0.2938 |        -0.3100 |     0.2366 |     2591 | CSI500  | factor_rotation_h20_w126_top4 | monthly_hold |      126 |       4 |              0.0030 |             0.0132 |                  -0.4313 |
|    0.0407 |    0.1423 |   0.2862 |        -0.2848 |     0.2188 |     2591 | CSI500  | factor_rotation_h20_w504_top4 | weekly_hold  |      504 |       4 |              0.0030 |             0.0132 |                  -0.4313 |
|    0.0424 |    0.1599 |   0.2650 |        -0.3167 |     0.3562 |     2591 | CSI500  | factor_rotation_h20_w126_top4 | top_quantile |      126 |       4 |              0.0030 |             0.0132 |                  -0.4313 |
|    0.0455 |    0.1751 |   0.2599 |        -0.4040 |     0.1757 |     1616 | STAR50  | factor_rotation_h20_w126_top8 | weekly_hold  |      126 |       8 |              0.0810 |             0.2379 |                  -0.6266 |

## 最近一年平均入选权重
| index   |   window |   top_n | factor                                   |   recent_avg_weight |
|:--------|---------:|--------:|:-----------------------------------------|--------------------:|
| CSI1000 |      126 |       4 | cf_crowding_mom20_beta_ratio_chg20       |              0.3168 |
| CSI1000 |      126 |       4 | cf_above_ma20_ratio_z                    |              0.3073 |
| CSI1000 |      504 |       4 | cf_amount_ratio20_top20_chg20            |              0.2690 |
| CSI1000 |      504 |       4 | cf_amount_ratio20_mean_chg20             |              0.2681 |
| CSI1000 |      126 |       4 | cf_mom20_median                          |              0.2651 |
| CSI1000 |      252 |       4 | cf_coverage                              |              0.2646 |
| CSI1000 |      126 |       4 | cf_crowding_mom20_amount_ratio_chg20     |              0.2646 |
| CSI1000 |      504 |       4 | cf_mom20_dispersion_chg20                |              0.2599 |
| CSI1000 |      126 |       4 | cf_crowding_amount20_vol_ratio_z         |              0.2596 |
| CSI1000 |      252 |       4 | cf_crowding_mom20_beta_ratio_chg20       |              0.2589 |
| CSI1000 |      126 |       4 | cf_spread_mom20_next_concentration_z     |              0.2586 |
| CSI1000 |      252 |       4 | cf_crowding_mom20_vol_ratio_chg20        |              0.2586 |
| CSI500  |      126 |       4 | cf_amp20_mean_chg20                      |              0.2797 |
| CSI500  |      252 |       4 | cf_crowding_mom20_vol_ratio_chg20        |              0.2647 |
| CSI500  |      126 |       4 | cf_amount_concentration_top20_chg20      |              0.2643 |
| CSI500  |      504 |       4 | cf_crowding_amount20_vol_ratio_chg20     |              0.2605 |
| CSI500  |      252 |       4 | cf_spread_amount20_next_concentration_z  |              0.2596 |
| CSI500  |      252 |       4 | cf_amount_ratio20_mean_chg20             |              0.2594 |
| CSI500  |      126 |       4 | cf_spread_amount20_next_concentration_z  |              0.2561 |
| CSI500  |      126 |       4 | cf_crowding_mom20_vol_ratio_z            |              0.2557 |
| CSI500  |      126 |       4 | cf_crowding_amount20_amount_ratio_chg20  |              0.2536 |
| CSI500  |      126 |       4 | cf_weight_concentration_top20            |              0.2533 |
| CSI500  |      252 |       4 | cf_crowding_amount20_vol_ratio           |              0.2533 |
| CSI500  |      504 |       4 | cf_amount_ratio20_top20                  |              0.2533 |
| STAR50  |      504 |       4 | cf_amount_ratio20_mean_chg20             |              0.2740 |
| STAR50  |      126 |       4 | cf_spread_mom20_next_concentration_chg20 |              0.2720 |
| STAR50  |      126 |       4 | cf_amount_concentration_top20_chg20      |              0.2662 |
| STAR50  |      126 |       4 | cf_spread_amount20_ret1d                 |              0.2584 |
| STAR50  |      252 |       4 | cf_amount_ratio20_top20                  |              0.2582 |
| STAR50  |      504 |       4 | cf_amount_ratio20_top20_chg20            |              0.2578 |
| STAR50  |      252 |       4 | cf_spread_mom20_next_concentration_chg20 |              0.2577 |
| STAR50  |      126 |       4 | cf_amount_ratio20_top20                  |              0.2576 |
| STAR50  |      252 |       4 | cf_crowding_mom20_vol_ratio_z            |              0.2566 |
| STAR50  |      252 |       4 | cf_crowding_mom20_amount_ratio_chg20     |              0.2560 |
| STAR50  |      126 |       4 | cf_crowding_mom20_amount_ratio_chg20     |              0.2552 |
| STAR50  |      126 |       4 | cf_weighted_above_ma20_chg20             |              0.2540 |