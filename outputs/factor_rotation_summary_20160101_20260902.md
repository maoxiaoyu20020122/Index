# 成分股穿透因子轮动结果

- 样本：20160101 至 20260902
- 目标：未来 20 日收益
- 规则：滚动窗口内按 ICIR、方向胜率、收益贡献筛选因子；仅保留胜率不低于 50% 的因子；按质量分数加权。

## 策略表现前二十
|   ann_ret |   ann_vol |   sharpe |   max_drawdown |   win_rate |   n_days | index   | strategy                      | mode         |   window |   top_n |   benchmark_ann_ret |   benchmark_sharpe |   benchmark_max_drawdown |
|----------:|----------:|---------:|---------------:|-----------:|---------:|:--------|:------------------------------|:-------------|---------:|--------:|--------------------:|-------------------:|-------------------------:|
|    0.1324 |    0.1457 |   0.9089 |        -0.1680 |     0.2019 |     2590 | CSI1000 | factor_rotation_h20_w504_top8 | weekly_hold  |      504 |       8 |             -0.0223 |            -0.0888 |                  -0.5726 |
|    0.1284 |    0.1532 |   0.8380 |        -0.2091 |     0.2135 |     2590 | CSI1000 | factor_rotation_h20_w504_top6 | weekly_hold  |      504 |       6 |             -0.0223 |            -0.0888 |                  -0.5726 |
|    0.0835 |    0.1232 |   0.6776 |        -0.2008 |     0.1865 |     2590 | CSI500  | factor_rotation_h20_w504_top8 | weekly_hold  |      504 |       8 |              0.0116 |             0.0506 |                  -0.4313 |
|    0.0807 |    0.1343 |   0.6010 |        -0.1728 |     0.1950 |     2590 | CSI500  | factor_rotation_h20_w504_top6 | weekly_hold  |      504 |       6 |              0.0116 |             0.0506 |                  -0.4313 |
|    0.1085 |    0.1858 |   0.5839 |        -0.2466 |     0.1330 |     1616 | STAR50  | factor_rotation_h20_w504_top8 | monthly_hold |      504 |       8 |              0.0810 |             0.2379 |                  -0.6266 |
|    0.0824 |    0.1488 |   0.5536 |        -0.2548 |     0.3568 |     2590 | CSI500  | factor_rotation_h20_w126_top4 | top_quantile |      126 |       4 |              0.0116 |             0.0506 |                  -0.4313 |
|    0.0819 |    0.1481 |   0.5534 |        -0.2873 |     0.2015 |     2590 | CSI1000 | factor_rotation_h20_w504_top4 | weekly_hold  |      504 |       4 |             -0.0223 |            -0.0888 |                  -0.5726 |
|    0.0747 |    0.1463 |   0.5105 |        -0.2267 |     0.1250 |     1616 | STAR50  | factor_rotation_h20_w504_top6 | weekly_hold  |      504 |       6 |              0.0810 |             0.2379 |                  -0.6266 |
|    0.0898 |    0.1759 |   0.5104 |        -0.1973 |     0.1361 |     1616 | STAR50  | factor_rotation_h20_w504_top4 | monthly_hold |      504 |       4 |              0.0810 |             0.2379 |                  -0.6266 |
|    0.0950 |    0.1892 |   0.5019 |        -0.2625 |     0.1392 |     1616 | STAR50  | factor_rotation_h20_w504_top4 | weekly_hold  |      504 |       4 |              0.0810 |             0.2379 |                  -0.6266 |
|    0.0964 |    0.1954 |   0.4931 |        -0.2373 |     0.1702 |     1616 | STAR50  | factor_rotation_h20_w252_top4 | weekly_hold  |      252 |       4 |              0.0810 |             0.2379 |                  -0.6266 |
|    0.0712 |    0.1510 |   0.4715 |        -0.2184 |     0.2193 |     2590 | CSI1000 | factor_rotation_h20_w126_top4 | weekly_hold  |      126 |       4 |             -0.0223 |            -0.0888 |                  -0.5726 |
|    0.0689 |    0.1467 |   0.4699 |        -0.2685 |     0.3529 |     2590 | CSI500  | factor_rotation_h20_w126_top6 | top_quantile |      126 |       6 |              0.0116 |             0.0506 |                  -0.4313 |
|    0.0584 |    0.1298 |   0.4501 |        -0.2721 |     0.1884 |     2590 | CSI500  | factor_rotation_h20_w504_top6 | monthly_hold |      504 |       6 |              0.0116 |             0.0506 |                  -0.4313 |
|    0.0660 |    0.1491 |   0.4430 |        -0.2817 |     0.1996 |     2590 | CSI1000 | factor_rotation_h20_w504_top8 | monthly_hold |      504 |       8 |             -0.0223 |            -0.0888 |                  -0.5726 |
|    0.0613 |    0.1453 |   0.4218 |        -0.2643 |     0.2162 |     2590 | CSI500  | factor_rotation_h20_w126_top4 | monthly_hold |      126 |       4 |              0.0116 |             0.0506 |                  -0.4313 |
|    0.0586 |    0.1430 |   0.4095 |        -0.2885 |     0.2112 |     2590 | CSI500  | factor_rotation_h20_w126_top6 | monthly_hold |      126 |       6 |              0.0116 |             0.0506 |                  -0.4313 |
|    0.0515 |    0.1461 |   0.3526 |        -0.2893 |     0.1973 |     2590 | CSI1000 | factor_rotation_h20_w504_top6 | monthly_hold |      504 |       6 |             -0.0223 |            -0.0888 |                  -0.5726 |
|    0.0492 |    0.1403 |   0.3510 |        -0.2816 |     0.3676 |     2590 | CSI500  | factor_rotation_h20_w504_top6 | top_quantile |      504 |       6 |              0.0116 |             0.0506 |                  -0.4313 |
|    0.0651 |    0.1906 |   0.3417 |        -0.3484 |     0.1677 |     1616 | STAR50  | factor_rotation_h20_w252_top8 | weekly_hold  |      252 |       8 |              0.0810 |             0.2379 |                  -0.6266 |

## 最近一年平均入选权重
| index   |   window |   top_n | factor                                   |   recent_avg_weight |
|:--------|---------:|--------:|:-----------------------------------------|--------------------:|
| CSI1000 |      126 |       4 | cf_crowding_mom20_beta_ratio_chg20       |              0.3263 |
| CSI1000 |      126 |       4 | cf_above_ma20_ratio_z                    |              0.3245 |
| CSI1000 |      126 |       4 | cf_crowding_amount20_beta_ratio_chg20    |              0.2801 |
| CSI1000 |      126 |       4 | cf_crowding_mom20_amp_ratio_z            |              0.2670 |
| CSI1000 |      504 |       4 | cf_amount_ratio20_top20_chg20            |              0.2640 |
| CSI1000 |      504 |       4 | cf_amount_ratio20_mean_chg20             |              0.2632 |
| CSI1000 |      126 |       4 | cf_crowding_mom20_amount_ratio_chg20     |              0.2627 |
| CSI1000 |      252 |       4 | cf_coverage                              |              0.2609 |
| CSI1000 |      126 |       4 | cf_crowding_amount20_vol_ratio_z         |              0.2598 |
| CSI1000 |      126 |       4 | cf_amount_concentration_top20_z          |              0.2596 |
| CSI1000 |      252 |       4 | cf_crowding_mom20_beta_ratio_chg20       |              0.2592 |
| CSI1000 |      252 |       4 | cf_crowding_mom20_vol_ratio_chg20        |              0.2578 |
| CSI500  |      126 |       4 | cf_amp20_mean_chg20                      |              0.2827 |
| CSI500  |      252 |       4 | cf_amount_ratio20_mean_chg20             |              0.2679 |
| CSI500  |      252 |       4 | cf_crowding_mom20_vol_ratio_chg20        |              0.2672 |
| CSI500  |      504 |       4 | cf_crowding_amount20_vol_ratio_chg20     |              0.2627 |
| CSI500  |      252 |       4 | cf_spread_amount20_next_concentration_z  |              0.2598 |
| CSI500  |      126 |       4 | cf_spread_amount20_next_concentration_z  |              0.2582 |
| CSI500  |      126 |       4 | cf_amount_concentration_top20_chg20      |              0.2582 |
| CSI500  |      252 |       4 | cf_crowding_mom20_amount_ratio_chg20     |              0.2541 |
| CSI500  |      126 |       4 | cf_weight_concentration_top20            |              0.2541 |
| CSI500  |      126 |       4 | cf_crowding_amount20_amount_ratio_chg20  |              0.2540 |
| CSI500  |      126 |       4 | cf_crowding_mom20_vol_ratio_z            |              0.2535 |
| CSI500  |      252 |       4 | cf_weight_concentration_top20            |              0.2535 |
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