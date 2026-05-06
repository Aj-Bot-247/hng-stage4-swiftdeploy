package swiftdeploy.infrastructure
import rego.v1

default allow := false

cpu_ok if {
    input.host.cpu_load <= input.limits.max_cpu_load
}

disk_ok if {
    input.host.disk_free_gb >= input.limits.min_disk_free_gb
}

allow if {
    cpu_ok
    disk_ok
}

reason contains msg if {
    not cpu_ok
    msg := sprintf("CPU load (%.2f) exceeds threshold (%.2f)", [input.host.cpu_load, input.limits.max_cpu_load])
}

reason contains msg if {
    not disk_ok
    msg := sprintf("Free disk space (%.2f GB) is below threshold (%.2f GB)", [input.host.disk_free_gb, input.limits.min_disk_free_gb])
}