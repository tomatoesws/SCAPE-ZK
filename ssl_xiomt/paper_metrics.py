PAPER_FACTS = {
    "paper": {
        "title": "SSL-XIoMT: Secure, Scalable, and Lightweight Cross-Domain IoMT Sharing With SSI and ZKP Authentication",
        "doi": "10.1109/OJCS.2025.3570087",
        "received": "2025-04-17",
        "accepted": "2025-05-11",
        "published": "2025-05-14",
        "current_version": "2025-06-02",
    },
    "environment": {
        "os": "Ubuntu 20.04",
        "cpu": "Intel Xeon E-2336 @ 2.9 GHz",
        "ram_gb": 16,
        "implementation": "Python",
        "libraries": [
            "PyCryptodome",
            "Charm-Crypto",
            "OpenSSL",
            "Docker-CP-ABE",
            "pairing-operation",
            "libstark",
            "bellman",
            "ACA-Py",
        ],
    },
    "proof_generation_verification": {
        "scope": "<= 1000 proofs",
        "scheme_31_seconds": 522.3,
        "scheme_29_seconds": 109.7,
        "ssl_xiomt_seconds_min": 69.4,
        "ssl_xiomt_seconds_max": 76.8,
    },
    "integrity_verification": {
        "ssl_xiomt_outperforms_latency_after_requests": 500,
        "ssl_xiomt_throughput_surpasses_after_concurrent_requests": 50,
        "ssl_xiomt_peak_verifications_per_second": 918,
        "scheme_31_peak_verifications_per_second": 777,
        "ssl_xiomt_peak_user_range": "100-150 users",
    },
    "secure_cross_domain_transmission": {
        "all_compared_schemes_under_seconds": 0.1,
    },
}
