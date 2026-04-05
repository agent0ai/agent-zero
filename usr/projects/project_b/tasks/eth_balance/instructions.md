Check the ETH balance of the following Ethereum wallet addresses and save the results.

Wallet addresses to check:
1. 0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe (Ethereum Foundation)
2. 0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8 (Binance Cold Wallet)
3. 0xDA9dfA130Df4dE4673b89022EE50ff26f6EA73Cf (Kraken)

Use a public Ethereum API or web3 library to fetch the current balances.

Create a JSON file called `balances.json` with the following structure:

```json
{
    "timestamp": "2025-01-26T12:00:00Z",
    "balances": [
        {
            "address": "0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe",
            "name": "Ethereum Foundation",
            "balance_wei": "123456789000000000000",
            "balance_eth": 123.456789
        },
        ...
    ],
    "total_eth": 12345.67
}
```

Requirements:
- Use ISO 8601 format for timestamp
- `balance_wei` should be a string (to handle large numbers)
- `balance_eth` should be a float with up to 6 decimal places
- `total_eth` is the sum of all `balance_eth` values
- All three addresses must be included