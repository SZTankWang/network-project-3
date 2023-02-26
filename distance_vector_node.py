from simulator.node import Node
import json 
import copy 



#routing message format: [dest, cost, path[] ], seq 
class Distance_Vector_Node(Node):
    def __init__(self, id):
        super().__init__(id)

        #key:destination, value: {cost:cost,path:path}
        self.table = {} 
        self.table[self.id] = {"cost":0,"path":[self.id]}
        self.link_cost = {}
        #to keep track the newest seq used by a neighbor. To deal with latency
        self.neighbor_seqs = {}
        #a dict to keep track of neighbor's table 
        self.neighbor_dvs = {}
        self.seq_num = 0

    # Return a json dump of self.table
    def __str__(self):
        #a string representation of the node's dv 
        message = copy.deepcopy(self.table)
        message["seq"] = self.seq_num
        #increment seq 
        self.seq_num += 1
        return json.dumps(message) 


    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        # latency = -1 if delete a link
        if latency == -1:
            #remove this neighbor from self.neighbor_dvs 
            del self.neighbor_dvs[neighbor] 
            del self.link_cost[neighbor]
            #else, don't change
        else:
            print(self.id,"says",neighbor,"has been updated",latency)
            #if first time knowing this link
            self.link_cost[neighbor] = latency 

        #recompute self.table

        self.recompute_table()


    def recompute_table(self):
        #create a new self.table 
        new_table = {}

        #for every entry in link_cost, fill the table using their value first
        for neighbor,cost in self.link_cost.items():
            new_table[neighbor] = {
                "cost":cost,
                "path":[self.id,neighbor]
            }


        #and then, we compute using neighbor_dvs information
        for neighbor,n_dvs in self.neighbor_dvs.items():
            if neighbor not in self.link_cost:
                return 

            cost_to_neighbor = self.link_cost[neighbor]
            for dest,vector in n_dvs.items():
                int_dest = int(dest)
                via_neighbor_to_dest = vector["cost"]+cost_to_neighbor
                #if dest in table, follow bellman equation
                if int_dest in new_table:
                    
                    if  via_neighbor_to_dest< new_table[int_dest]["cost"]:
                        new_table[int_dest] = {
                            "cost":via_neighbor_to_dest,
                            "path":[self.id]+vector["path"]
                        }
                #if not in table, add new entry 
                else:
                    new_table[int_dest] = {
                        "cost":via_neighbor_to_dest,
                        "path":[self.id]+vector["path"]
                    }
        #has self.table changed? 
        if new_table != self.table:
            #notify neighbor
            self.table = new_table 
            self.broadcast()

    def broadcast(self):
        self.send_to_neighbors(str(self))



    # Fill in this function
    def process_incoming_routing_message(self, m):
        #message format: dictionary<{dest:xxx,cost:xxx,path:[xxx]}>
        message = json.loads(m)
        print("node",self.id,"receive\n",message)
        #come from
        neighbor = int(message[next(iter(message))]["path"][0])
        
        #firstly, is this out of date
        seq = message["seq"]
        if neighbor in self.neighbor_seqs and seq < self.neighbor_seqs[neighbor]:
            return 
        self.neighbor_seqs[neighbor] = seq 
        
        del message["seq"]
        
        #process incoming neighbor's dv. There are things
        # in self.neighbor_dv we might need to delete(when the link no longer exist)
        # there are also info we are not gonna accept (when path contains loop)
        # check if any new path contains loop 
        to_delete = []
        for dest,vector in message.items():
        
            if self.id in vector["path"]:
                to_delete.append(dest)
        
        for d in to_delete:
            del message[d]
        
        #replace neighbor_dv[neighbor] with the new message 
        self.neighbor_dvs[neighbor] = message 

        #bellman-ford process
        self.recompute_table()





    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        print("getting next hop at",self.id,":",self.table)
        print("destination is",destination)

        if destination not in self.table:
            return -1 
        return self.table[destination]["path"][1]
        
