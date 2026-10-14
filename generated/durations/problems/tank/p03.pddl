(define (problem tank-3) (:domain tank) (:objects t1 t2 t3 - tank)
(:init (closed t1) (unused t1) (= (level t1) 0) (= (flow t1) 2) (= (low t1) 30) (= (high t1) 34) (closed t2) (unused t2) (= (level t2) 0) (= (flow t2) 3) (= (low t2) 34) (= (high t2) 38) (closed t3) (unused t3) (= (level t3) 0) (= (flow t3) 4) (= (low t3) 38) (= (high t3) 42))
(:goal (and (ready t1) (ready t2) (ready t3))))
