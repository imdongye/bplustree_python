'''
im dongye / 23-06-02

leaf is same height, inner node has m/2 children.

order is assumed to be odd => convenient when creating a new root node

'''

import sys

def ceil(x):
    return int(x//1+bool(x%1))

class Node:
    def __init__(self):
        # ceil(order/2)-1 <= nr키 <= order-1
        self.keys = []
        # ceil(order/2) <= nr서브트리 <= order
        self.subTrees = []
        # None이면 루트
        self.parent = None
        self.isLeaf = False
        # leaf일때 같은층의 다음 leaf연결
        self.nextNode = None
        # nr키 == nr값
        self.values = []
        return
    
    def keys_to_str(self):
        l = "["
        for k in self.keys:
            l += "{},".format(k)
        l = l[:-1] + "]"
        return l
        
    def find_down_idx(self, k):
        nr_keys = len(self.keys)
        for i in range(nr_keys):
            if k < self.keys[i]:
                return i
        return nr_keys
    
    def find_sub_idx(self, sub):
        sub_idx=0
        while not self.subTrees[sub_idx] is sub:
            sub_idx+=1
        return sub_idx
    
    #*** 왼쪽leaf찾기
    # split할때 left right두개를 만들고 leaf의 왼쪽과 연결할때 사용했는데 cur을 그냥 사용함.
    # delete_rebalancing할때 필요할줄알았는데 같은부모에서의 왼쪽과 오른쪽만을 사용함
    def find_left_leaf(self):
        if not self.isLeaf:
            return None
        top = self.parent
        leaf_key = self.keys[0]
        cur_idx = top.find_down_idx(leaf_key)
        # insert한 곳이 왼쪽이 아닐때까지 올라가기
        while cur_idx==0:
            top = top.parent
            if top == None:
                return None
            cur_idx = top.find_subset_idx(cur_idx)
        
        down = top.subTrees[cur_idx-1]
        #왼쪽에 서브트리가있는곳까지 왔으면 계속 오른쪽으로 내려간다.
        while not down.isLeaf:
            last_idx = len(down.subTrees)-1
            down = down.subTrees[last_idx]

        return down


class B_PLUS_TREE:
    def __init__(self, order):
        self.order = order
        self.MIN_NR_KEYS = ceil(order/2)-1 
        self.root = Node()
        self.root.isLeaf = True
        return
    
    #*** 과적 시켜놓은것을 분리
    def __split(self, cur):
        # cur가 leaf일때 left의 nextNode이기 때문에 유지한다. left = cur
        right = Node()
        mid_idx = len(cur.keys)//2
        mid_key = cur.keys[mid_idx]

        if cur.isLeaf:
            right.isLeaf = True
            right.keys = cur.keys[mid_idx:]
            cur.keys = cur.keys[:mid_idx]
            right.values = cur.values[mid_idx:]
            cur.values = cur.values[:mid_idx]
            right.nextNode = cur.nextNode
            cur.nextNode = right
        else: # 중간노드면 중간키는 위로 올린다.
            right.keys = cur.keys[mid_idx+1:]
            cur.keys = cur.keys[:mid_idx]
            right.subTrees = cur.subTrees[mid_idx+1:]
            cur.subTrees = cur.subTrees[:mid_idx+1]
            # subTree에게 전파!!
            for down in cur.subTrees:
                down.parent = cur
            for down in right.subTrees:
                down.parent = right

        # 루트면
        if cur.parent == None:
            top = Node()
            top.keys = [mid_key]
            top.subTrees = [cur, right]
            cur.parent = top; right.parent = top
            self.root = top
            return
        
        # 상위노드가 있고
        top = cur.parent
        left_idx = top.find_sub_idx(cur)
        top.keys.insert(left_idx, mid_key)
        top.subTrees.insert(left_idx+1, right)
        right.parent = top

        # 꽉 찻으면
        if len(top.keys) > self.order-1:
            self.__split(top)
        return
    
    #*** 추가
    def insert(self, k):        
        cur = self.root

        # leaf찾기
        while not cur.isLeaf:
            idx = cur.find_down_idx(k)
            cur = cur.subTrees[idx]

        insert_idx = cur.find_down_idx(k)
        cur.keys.insert(insert_idx, k)
        cur.values.insert(insert_idx, k)

        # leaf에 공간이 없으면
        if len(cur.keys) > self.order-1:
            self.__split(cur)
        return
    

    #*** 합치기 
    def __merge(self, cur, right):
        top = cur.parent

        top_idx = top.find_sub_idx(cur)

        if cur.isLeaf:
            cur.keys = cur.keys + right.keys
            cur.values = cur.values + right.values
            cur.nextNode = right.nextNode
        
        # 중간노드면 top의 키를 right subtree들을 구분하기위해 필요함 
        else:
            cur.keys.append(top.keys[top_idx])
            cur.keys = cur.keys + right.keys
            for right_sub in right.subTrees:
                right_sub.parent = cur
            cur.subTrees = cur.subTrees + right.subTrees
        
        # 상위 index key 수정될때 왼쪽이 없어서 None으로 된게 여기서 삭제됨
        top.keys.pop(top_idx)
        top.subTrees.pop(top_idx+1)

        return cur

    def __borrow_from_left(self, left, cur):
        top = cur.parent
        top_idx = top.find_sub_idx(cur)

        # left의 뒤에서 가져오고 상위 키 업데이트
        if cur.isLeaf:
            cur.keys.insert(0, left.keys.pop())
            cur.values.insert(0, left.values.pop())
            top.keys[top_idx-1] = cur.keys[0]
            
        # inter에서 top에서 받고 top을 빌린 left키로 대체 
        else:
            cur.keys.insert(0, top.keys[top_idx-1])

            cur.subTrees.insert(0, left.subTrees.pop())
            cur.subTrees[0].parent = cur

            top.keys[top_idx-1] = left.keys.pop()

        return cur
    
    def __borrow_from_right(self, cur, right):
        top = cur.parent
        top_idx = top.find_sub_idx(cur)

        # right의 처음에서 가져오고 상위 키 업데이트
        if cur.isLeaf:
            cur.keys.append(right.keys.pop(0))
            cur.values.append(right.values.pop(0))
            top.keys[top_idx] = right.keys[0]

        # top에서 키를 가져오고 right_key.pol(0)
        # sub_idx == nextkey_idx
        else:
            cur.keys.append(top.keys[top_idx])

            cur.subTrees.append(right.subTrees.pop(0))
            cur.subTrees[-1].parent = cur

            # right.keys의 첫번째를 없애고난뒤
            # 새로운 첫번째 key를 top key로 넣을수있지만
            # 더 작은값이 tree의 분포를 유지하는데 좋을것같고
            # leaf의 키값과 다른 inter 키가 있는게 성능상에도 좋을것같다.
            top.keys[top_idx] = right.keys.pop(0)

        return cur

    '''
    1. 현재 노드의 키개수가 최소키값보다 작고  왼쪽노드의 키개수가 최소키값보다 크면 왼쪽 노드에서 키를 가져온다.
    2. 아니면 현재 노드의 키개수가 최소키값보다 작고 오른쪽노드의 키개수가 최소키값보다 크면 오른쪽 노드에서 키를 가져온다.
    3. 아니면 왼쪽노드와 병합하고
    4. 아니면 오른쪽 노드와 병합한다.
    From: https://www.youtube.com/watch?v=pGOdeCpuwpI
    '''
    def __rebalance_for_delete(self, cur):
        if len(cur.keys) >= self.MIN_NR_KEYS:
            return
        
        top = cur.parent

        # root이고 키가 없을때 남은 sub를 root로
        if top == None and len(cur.keys) == 0:
            self.root = cur.subTrees[0]
            if self.root != None:
                self.root.parent = None
            return
        if top == None:
            return
        
        top_idx = top.find_sub_idx(cur)
        
        left = top.subTrees[top_idx-1] if top_idx>0 else None
        right = top.subTrees[top_idx+1] if top_idx+1<len(top.subTrees) else None

        if left!=None and len(left.keys) > self.MIN_NR_KEYS:
            self.__borrow_from_left(left, cur)

        elif right!=None and len(right.keys) > self.MIN_NR_KEYS:
            self.__borrow_from_right(cur, right)

        # 왼쪽이 없으면 4순위
        elif top_idx == 0:
            merged = self.__merge(cur, right)
            self.__rebalance_for_delete(merged.parent)
        
        # 왼쪽있는경우 다 왼쪽으로
        else:
            merged = self.__merge(left, cur)
            self.__rebalance_for_delete(merged.parent)

        return

    #*** 삭제
    def delete(self, k):
        cur = self.root
        key_node = None

        # leaf찾기
        while not cur.isLeaf:
            idx = cur.find_down_idx(k)
            if cur.keys[idx-1] == k:
                key_node = cur
            cur = cur.subTrees[idx]

        del_idx = cur.keys.index(k)
        cur.keys.pop(del_idx)
        cur.values.pop(del_idx)

        top = cur.parent
        if top==None:
            return
        
        # 키 인덱스노드를 다음키로 수정
        if key_node!=None:
            top_idx = top.find_sub_idx(cur)
            replace_key = None

            if len(cur.keys) == 0:
                if top_idx == len(top.subTrees)-1:
                    replace_key = None
                else:
                    replace_key = top.subTrees[top_idx].keys[0]
            else:
                replace_key = cur.keys[0]
            

            replace_idx = key_node.keys.index(k)
            key_node.keys[replace_idx] = replace_key

        # 최소개수 만족하면 끝
        if self.MIN_NR_KEYS <= len(cur.keys):
            return

        # 최소보다 작아졌을경우 4단계
        self.__rebalance_for_delete(cur)
        return
    

    #*** 루트 출력
    def print_root(self):
        # print(self.root.keys_to_str())
        l = "["
        for k in self.root.keys:
            l += "{},".format(k)
        l = l[:-1] + "]"
        print(l) 
        return
    
    #*** 트리 출력
    def print_tree(self):
        if self.root.isLeaf:
            print(self.root.keys_to_str())
            return
        
        print_queue = [self.root]
        
        # BFS
        while len(print_queue) > 0:
            l=""
            cur = print_queue.pop(0)
            l+=cur.keys_to_str()
            l+="-"
            
            for down in cur.subTrees:
                l+=down.keys_to_str()+","

            print(l[:-1])

            if not cur.subTrees[0].isLeaf:
                print_queue += cur.subTrees
        return

    #*** 두 key 사이 값 전부 출력 
    def find_range(self, k_from, k_to):
        # from에 해당하는 leaf까지 가기
        cur = self.root
        l = ""

        while not cur.isLeaf:
            down_idx = cur.find_down_idx(k_from)
            cur = cur.subTrees[down_idx]

        while cur != None:
            for i in range(len(cur.keys)):
                if k_to < cur.keys[i]:
                    cur = None
                    break
                if k_from <= cur.keys[i]:
                    l += "{},".format(cur.values[i])
            if cur != None:
                cur = cur.nextNode
        l=l[:-1]
        print(l)
        return
        
    #*** k의 path출력
    def find(self, k):
        cur = self.root
        path = cur.keys_to_str()

        while not cur.isLeaf:
            down_idx = cur.find_down_idx(k)
            cur = cur.subTrees[down_idx]
            path += "-"+cur.keys_to_str()
            
        if k in cur.keys:
            print(path)
        else:
            print("NONE")
        return



def main():
    '''
    Input: test_bp.txt
    Output: result.txt
    '''
    sys.stdin = open("test1.txt",'r')
    sys.stdout = open("result.txt","w")
    myTree = None
    
    while (True):
        comm = sys.stdin.readline()
        comm = comm.replace("\n", "")
        params = comm.split()
        if len(params) < 1:
            continue
        
        print(comm)
        
        if params[0] == "INIT":
            order = int(params[1])
            myTree = B_PLUS_TREE(order)
            
        elif params[0] == "EXIT":
            break
            
        elif params[0] == "INSERT":
            k = int(params[1])
            myTree.insert(k)
            
        elif params[0] == "DELETE":
            k = int(params[1])
            myTree.delete(k)            
            
        elif params[0] == "ROOT":            
            myTree.print_root()            
            
        elif params[0] == "PRINT":            
            myTree.print_tree()            
                  
        elif params[0] == "FIND":            
            k = int(params[1])
            myTree.find(k)
            
        elif params[0] == "RANGE":            
            k_from = int(params[1])
            k_to = int(params[2])
            myTree.find_range(k_from, k_to)
        
        elif params[0] == "SEP":
            print("-------------------------")

    return


if __name__ == "__main__":
    main()