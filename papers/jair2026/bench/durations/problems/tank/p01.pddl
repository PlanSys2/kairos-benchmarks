(define (problem tank-1) (:domain tank) (:objects t1 - tank)
(:init (closed t1) (unused t1) (= (level t1) 0) (= (flow t1) 2) (= (low t1) 30) (= (high t1) 34))
(:goal (and (ready t1))))
