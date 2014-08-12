# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import boto.ec2
import boto.vpc
import logging

logger = logging.getLogger(__name__)


class AWS(object):
    
    _ec2_connection = None
    _vpc_connection = None

    def __init__(self, access_key=None, secret_key=None):
        self.access_key = access_key
        self.secret_key = secret_key
        self._security_groups = {}

    def get_ec2_connection(self, region):
        if not self._ec2_connection:
            self._ec2_connection =  boto.ec2.connect_to_region(
                    region,
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key)
        return self._ec2_connection

    def get_vpc_connection(self, region):
        if not self._vpc_connection:
            conn = self.get_ec2_connection(region)
            self._vpc_connection = boto.vpc.VPCConnection(
                    region=conn.region,
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key)
        return self._vpc_connection

    def all_regions(self, ):
        regions = boto.ec2.regions()
        return [r.name for r in regions]

    def get_all_subnets(self, regions):
        all_subnets = {}
        for region in regions:
            logger.debug("fetching subnets in %s" % region)
            conn = self.get_vpc_connection(region)
            for subnet in conn.get_all_subnets():
                all_subnets[subnet.id] = subnet
        return all_subnets

    def get_all_instances(self, regions):
        all_instances = {}
        for region in regions:
            logger.debug("fetching instances in %s" % region)
            conn = self.get_ec2_connection(region)
            for instance in conn.get_only_instances():
                all_instances[instance.id] = instance
        return all_instances

    def get_security_group(self, sgid):
        if sgid in self._security_groups:
            return self._security_groups[sgid]
        logger.debug("fetching security group %s in %s", sgid.id, sgid.region)
        conn = self.get_ec2_connection(sgid.region)
        sgs = conn.get_all_security_groups(group_ids=[sgid.id])
        if not sgs:
            return None
        sg = sgs[0]
        # verify it doesn't have outbound rules
        msg = "fwunit assumes outbound rules are unrestricted (the default)"
        assert len(sg.rules_egress) == 1, msg
        assert sg.rules_egress[0].ip_protocol == "-1", msg
        assert sg.rules_egress[0].from_port == None, msg
        assert sg.rules_egress[0].to_port == None, msg
        self._security_groups[sgid] = sg
        return sg
