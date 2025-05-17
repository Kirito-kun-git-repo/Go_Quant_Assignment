# Trading Simulator Sequence Diagram

This document provides a sequence diagram showing the interaction between different components of the trading simulator.

## Market Data Flow Sequence

```mermaid
sequenceDiagram
    participant User
    participant UI as UI Interface
    participant App as Application Controller
    participant DataFeed as Market Data Feed
    participant OrderBook as OrderBook
    participant Impact as Impact Models
    participant Fee as Fee Calculator
    participant Maker as Maker/Taker Classifier

    User->>UI: Start Application
    UI->>App: Initialize
    App->>OrderBook: Create OrderBook
    App->>UI: Display Initial UI

    User->>UI: Click "Start Feed"
    UI->>App: Start Market Data Feed
    App->>DataFeed: Initialize WebSocket
    
    loop Every Market Tick
        DataFeed->>DataFeed: Receive Tick Data
        DataFeed->>App: Forward Tick Data
        App->>OrderBook: update_from_tick(tick)
        OrderBook->>OrderBook: Update Bids/Asks
        OrderBook->>OrderBook: Calculate Volatility
        App->>UI: Update Market Display
    end

    User->>UI: Enter Order Quantity
    User->>UI: Select Fee Tier
    User->>UI: Click "Buy" or "Sell"
    UI->>App: Calculate Trade Impact
    
    App->>OrderBook: Get Current State
    App->>Impact: calculate_total_impact(orderbook, qty)
    Impact->>Impact: Calculate Permanent Impact
    Impact->>Impact: Calculate Temporary Impact
    Impact-->>App: Return Impact Values
    
    App->>OrderBook: Get Current State
    App->>App: simulate_slippage(qty, orderbook, side)
    
    App->>Maker: classify_order_heuristic(qty, orderbook, side)
    Maker-->>App: Return Classification
    App->>Fee: compute_fee(qty, price, tier, is_taker)
    Fee-->>App: Return Fee Amount
    
    App->>App: Calculate Net Cost
    App->>UI: Update Trade Impact Display
    UI-->>User: Display Results
    
    User->>UI: Click "Stop Feed"
    UI->>App: Stop Market Data Feed
    App->>DataFeed: Close WebSocket
    
    User->>UI: Exit Application
    UI->>App: Cleanup Resources
    App->>App: Terminate
```

## Benchmarking Sequence

```mermaid
sequenceDiagram
    participant User
    participant Benchmark as Benchmark Script
    participant OrderBook as OrderBook
    participant Impact as Impact Models
    participant Charts as Chart Generator
    
    User->>Benchmark: Run Benchmark
    
    Benchmark->>Benchmark: Initialize Parameters
    
    Benchmark->>OrderBook: Create OrderBook
    
    loop For Each Load Level
        Benchmark->>Benchmark: Generate Synthetic Ticks
        Benchmark->>OrderBook: Measure Update Time
        OrderBook-->>Benchmark: Return Results
    end
    
    Benchmark->>OrderBook: Create OrderBook
    Benchmark->>Benchmark: Initialize OrderBook
    
    loop For Each Load Level
        Benchmark->>Impact: Measure Calculation Time
        Impact-->>Benchmark: Return Results
    end
    
    Benchmark->>OrderBook: Create OrderBook
    Benchmark->>Benchmark: Initialize OrderBook
    
    loop For Each Load Level
        Benchmark->>Benchmark: Measure End-to-End Latency
        Benchmark->>Benchmark: Record Results
    end
    
    Benchmark->>Benchmark: Compile Results
    Benchmark->>Benchmark: Save to JSON
    
    Benchmark->>Charts: Generate Performance Charts
    Charts->>Charts: Create Latency vs. Load Charts
    Charts->>Charts: Create Distribution Charts
    
    Benchmark-->>User: Display Summary
```

## UI Interaction Sequence

```mermaid
sequenceDiagram
    participant User
    participant UI as UI Interface
    participant App as Application Controller
    participant Thread as Background Thread
    
    User->>UI: Launch Application
    UI->>App: Initialize
    App->>Thread: Create Background Thread
    App->>UI: Display Initial UI
    
    User->>UI: Change Symbol
    UI->>App: Update Symbol
    App->>App: Reset OrderBook
    
    User->>UI: Change Quantity
    UI->>App: Update Quantity
    App->>App: Recalculate Impact
    App->>UI: Update Display
    
    User->>UI: Click "Start Feed"
    UI->>App: Start Feed
    App->>Thread: Start Background Processing
    
    loop Background Processing
        Thread->>Thread: Generate/Receive Market Data
        Thread->>App: Update OrderBook
        App->>UI: Update Market Display
    end
    
    User->>UI: Click "Buy"
    UI->>App: Process Buy Order
    App->>App: Calculate Trade Impact
    App->>UI: Update Trade Impact Display
    
    User->>UI: Click "Stop Feed"
    UI->>App: Stop Feed
    App->>Thread: Stop Background Processing
    
    User->>UI: Close Window
    UI->>App: Exit Application
    App->>Thread: Terminate Thread
    App->>App: Cleanup Resources
```

## Integration Test Sequence

```mermaid
sequenceDiagram
    participant Test as Integration Test
    participant OrderBook as OrderBook
    participant UI as Mock UI
    participant App as Application Logic
    
    Test->>Test: Initialize Test Environment
    Test->>OrderBook: Create Test OrderBook
    Test->>UI: Create Mock UI
    
    Test->>Test: Generate Test Ticks
    
    loop Rapid Tick Ingestion Test
        Test->>OrderBook: update_from_tick(tick)
        Test->>App: update_market_data_display(window, snapshot)
        App->>UI: Update UI Elements
    end
    
    Test->>Test: Measure Processing Time
    Test->>Test: Assert Latency Within Threshold
    
    loop Trade Impact Calculation Test
        Test->>App: update_trade_impact(window, side)
        App->>OrderBook: Get OrderBook State
        App->>App: Calculate Slippage, Fee, Impact
        App->>UI: Update UI Elements
    end
    
    Test->>Test: Measure Calculation Time
    Test->>Test: Assert Latency Within Threshold
    
    Test->>Test: End-to-End Workflow Test
    Test->>OrderBook: update_from_tick(tick)
    Test->>App: update_market_data_display(window, snapshot)
    Test->>App: update_trade_impact(window, side)
    
    Test->>Test: Verify All UI Elements Updated
    Test-->>Test: Report Test Results
```

These sequence diagrams illustrate the key interactions between different components of the trading simulator, including market data flow, benchmarking process, UI interactions, and integration testing.

The diagrams use Mermaid syntax, which can be rendered by many Markdown viewers including GitHub, GitLab, and various Markdown editors.