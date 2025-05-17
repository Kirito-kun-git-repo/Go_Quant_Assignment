# Trading Simulator Class Diagram

This document provides a class diagram showing the structure and relationships between different components of the trading simulator.

## Main Components

```mermaid
classDiagram
    class OrderBook {
        -symbol
        -bids
        -asks
        -mid_prices
        -timestamps
        -volatility
        +update_from_tick()
        +best_bid()
        +best_ask()
        +mid_price()
        +spread()
        +rolling_volatility()
        +get_volume()
    }
    
    class MarketDataFeed {
        -url
        -symbol
        -ws
        -callback
        +start()
        +stop()
        +is_running()
        -_on_message()
        -_connect()
        -_disconnect()
    }
    
    class FeeCalculator {
        +compute_fee()
        -_get_fee_rate()
    }
    
    class SlippageSimulator {
        +simulate_slippage()
        -_walk_book()
    }
    
    class ImpactModel {
        +calculate_total_impact()
        -_calculate_permanent_impact()
        -_calculate_temporary_impact()
    }
    
    class MakerTakerClassifier {
        +classify_order_heuristic()
        +classify_order_ml()
        -_extract_features()
    }
    
    class ApplicationController {
        -orderbook
        -data_feed
        -window
        -config
        +initialize()
        +start_feed()
        +stop_feed()
        +update_market_data_display()
        +update_trade_impact()
        +handle_event()
        -_process_tick()
        -_calculate_trade_metrics()
    }
    
    class UIManager {
        -window
        -theme
        -layout
        +create_window()
        +update_market_data()
        +update_trade_impact()
        +handle_events()
        -_create_layout()
        -_create_market_frame()
        -_create_trade_frame()
    }
    
    class BenchmarkManager {
        +benchmark_orderbook_updates()
        +benchmark_trade_impact()
        +benchmark_end_to_end()
        +run_benchmarks()
        +save_results()
        +generate_charts()
    }
    
    OrderBook <-- ApplicationController
    MarketDataFeed <-- ApplicationController
    UIManager <-- ApplicationController
    FeeCalculator <-- ApplicationController
    SlippageSimulator <-- ApplicationController
    ImpactModel <-- ApplicationController
    MakerTakerClassifier <-- ApplicationController
    
    OrderBook <-- BenchmarkManager
    ImpactModel <-- BenchmarkManager
    FeeCalculator <-- BenchmarkManager
    SlippageSimulator <-- BenchmarkManager
    MakerTakerClassifier <-- BenchmarkManager
```

## UI Components

```mermaid
classDiagram
    class UIManager {
        -window
        -theme
        -layout
        +create_window()
        +update_market_data()
        +update_trade_impact()
        +handle_events()
        -_create_layout()
        -_create_market_frame()
        -_create_trade_frame()
        -_create_control_frame()
    }
    
    class MarketDataDisplay {
        -window
        +update()
        -_format_mid_price()
        -_format_spread()
        -_format_volatility()
        -_format_timestamp()
    }
    
    class TradeImpactDisplay {
        -window
        +update()
        -_format_slippage()
        -_format_fee()
        -_format_impact()
        -_format_net_cost()
        -_format_classification()
    }
    
    class ControlPanel {
        -window
        +get_values()
        +handle_event()
        -_validate_quantity()
        -_validate_tier()
    }
    
    UIManager *-- MarketDataDisplay
    UIManager *-- TradeImpactDisplay
    UIManager *-- ControlPanel
```

## Benchmark and Testing Components

```mermaid
classDiagram
    class BenchmarkManager {
        +benchmark_orderbook_updates()
        +benchmark_trade_impact()
        +benchmark_end_to_end()
        +run_benchmarks()
        +save_results()
        +generate_charts()
        -_generate_synthetic_tick()
    }
    
    class ChartGenerator {
        +create_update_latency_chart()
        +create_impact_latency_chart()
        +create_e2e_latency_chart()
        +create_latency_distribution_chart()
        +create_comparison_chart()
        -_setup_figure()
        -_save_figure()
    }
    
    class ReportGenerator {
        +generate_report()
        -_create_title_page()
        -_create_charts_pages()
        -_create_summary_page()
    }
    
    class IntegrationTest {
        +test_rapid_tick_ingestion()
        +test_trade_impact_calculation_latency()
        +test_end_to_end_workflow()
        -_create_test_orderbook()
        -_create_mock_window()
        -_generate_test_ticks()
    }
    
    BenchmarkManager --> ChartGenerator
    BenchmarkManager --> ReportGenerator
```

These class diagrams illustrate the structure and relationships between the different components of the trading simulator, providing a comprehensive view of the system architecture.

The diagrams use Mermaid syntax, which can be rendered by many Markdown viewers including GitHub, GitLab, and various Markdown editors.