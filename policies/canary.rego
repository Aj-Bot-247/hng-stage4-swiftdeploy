package swiftdeploy.canary
import rego.v1

default allow := false

latency_ok if {
    input.metrics.p99_latency_ms <= input.limits.max_p99_latency_ms
}

error_rate_ok if {
    input.metrics.error_rate_percent <= input.limits.max_error_rate_percent
}

allow if {
    latency_ok
    error_rate_ok
}

reason contains msg if {
    not latency_ok
    msg := sprintf("P99 Latency (%.2f ms) exceeds threshold (%.2f ms)", [input.metrics.p99_latency_ms, input.limits.max_p99_latency_ms])
}

reason contains msg if {
    not error_rate_ok
    msg := sprintf("Error rate (%.2f%%) exceeds threshold (%.2f%%)", [input.metrics.error_rate_percent, input.limits.max_error_rate_percent])
}