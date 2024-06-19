<?php
require_once "app.php";
require_once "../config.php";

require_once "../terminal_web/calculate.php";

// esto no deberia de estar pero quiero hacerlo rapido
// y esta es la solucion mas rapida
require '../Controllers/toArray.php';
// ============================

$app->action("GET", "find", function ($parking, $value) use ($app) {
    
    $stays_list = [];
    $users_list = [];
    $articles_list = [];

    $valueAlpa = strtoupper($value);

    if(strlen($value) == 14){ //CODIGO DE BARRAS
        $stays = $app->em->getRepository("Stay")->createQueryBuilder('s')
        ->innerJoin("s.parking", "p")
        ->where("p.id = :parking")
        ->andWhere("s.DateLeave is null")
        ->andWhere("s.rate is not null")
        ->andWhere("s.barcode  =:value")
        ->setParameter("parking", $parking)
        ->setParameter("value", $value)
        ->setMaxResults(10)
        ->getQuery()
        ->getResult();
        
        foreach($stays as $stay) {
        $user = $stay->getUser();
        $rate = $stay->getUser();
        $vehicle = $stay->getVehicle();
        $parking = $stay->getParking();
        
        $s = toArrayComplejo($stay, $app->em);
        
        $s['discounts'] = [];
        foreach($stay->getDiscounts() as $discount) {
            $o = toArray($discount, $app->em);
            $o['name'] = $discount->getAgreement()->getName();
            
            $s['discounts'][] = $o;
        }
        
        $s['vehicle'] = $vehicle ? $vehicle->getPlate() : "";
        $s['parking'] = $parking->getName();
        $stays_list[] = $s;
        }
        
        return new Response("Ok", ["Stay" => $stays_list,"User" => $users_list,"Article" => $articles_list,]);
        
        
    }
    elseif(substr($valueAlpa, 0, 2) === 'NC'){ //ALFANUMERICO
        $alpha = substr($valueAlpa, -3);
        $stays = $app->em->getRepository("Stay")->createQueryBuilder('s')
            ->innerJoin("s.parking", "p")
            ->where("p.id =:parking")
            ->andWhere("s.DateLeave is null")
            ->andWhere("s.rate is not null")
            ->andWhere("s.alphanumericcode =:value")
            ->setParameter("parking", $parking)
            ->setParameter("value", $alpha)
            ->orderBy("s.DateJoin","DESC")
            ->setMaxResults(1)
            ->getQuery()
            ->getResult();
            
            foreach($stays as $stay) {
            $user = $stay->getUser();
            $rate = $stay->getUser();
            $vehicle = $stay->getVehicle();
            $parking = $stay->getParking();
            
            $s = toArrayComplejo($stay, $app->em);
            
            $s['discounts'] = [];
            foreach($stay->getDiscounts() as $discount) {
                $o = toArray($discount, $app->em);
                $o['name'] = $discount->getAgreement()->getName();
                
                $s['discounts'][] = $o;
            }
            
            $s['vehicle'] = $vehicle ? $vehicle->getPlate() : "";
            $s['parking'] = $parking->getName();
            $stays_list[] = $s;
            }
        
        return new Response("Ok", ["Stay" => $stays_list,"User" => $users_list,"Article" => $articles_list,]);
    }

    $alpha = '';
    $stays = $app->em->getRepository("Stay")->createQueryBuilder('s')
        ->innerJoin("s.parking", "p")
        ->innerJoin("s.vehicle", "v")
        ->where("p.id = :parking")
        ->andWhere("s.DateLeave is null")
        ->andWhere("s.rate is not null")
        ->andWhere("s.vehicle is not null and v.plate =:value")
        ->setParameter("parking", $parking)
        ->setParameter("value", $value)
        ->setMaxResults(10)
        ->getQuery()
        ->getResult();
		
        foreach($stays as $stay) {
            $user = $stay->getUser();
            $rate = $stay->getUser();
            $vehicle = $stay->getVehicle();
            $parking = $stay->getParking();
            
            $s = toArrayComplejo($stay, $app->em);
            
            $s['discounts'] = [];
            foreach($stay->getDiscounts() as $discount) {
                $o = toArray($discount, $app->em);
                $o['name'] = $discount->getAgreement()->getName();
                
                $s['discounts'][] = $o;
            }
            
            $s['vehicle'] = $vehicle ? $vehicle->getPlate() : "";
            $s['parking'] = $parking->getName();
            $stays_list[] = $s;
        }

    if($stays){
        return new Response("Ok", ["Stay" => $stays_list,"User" => $users_list,"Article" => $articles_list,]);
    }

    $users = $app->em->getRepository("User")->createQueryBuilder('u')
        ->innerJoin("u.usertype", "ut")
        ->innerJoin("ut.parkings", "p")
        ->where("p.id = :parking")
        ->andWhere("u.active = 1")
        ->andWhere("u.enabled = 1")
        ->andWhere("u.employee = 0")
        ->andWhere("(
				u.name like :value or
				u.lastname like :value or
				u.identitycard like :value or
			    u.number like :value)
			")
        ->setParameter("parking", $parking)
        ->setParameter("value", '%' . $value . '%')
        ->getQuery()
        ->getResult();

    

    foreach ($users as $user) {
        $rate = $app->em->getRepository("RateStay")
            ->findOneBy(["id" => $user->getUsertype()->getRate()->getId()]);

        if (!$rate) {
            $usertype = $user->getUsertype();

            $usr = toArrayComplejo($user, $app->em);

            $monthly = $app->em->getRepository('Monthly')->createQueryBuilder('m')
                ->where("m.user = :user")
                ->andWhere("m.active = 1")
                ->andWhere("m.paid = 1")
                ->setParameter('user', $user->getId())
                ->orderBy("m.endDate", "desc")
                ->getQuery()
                ->setMaxResults(1)
                ->getResult();

            if (count($monthly) >= 1) {
                $usr['monthly'] = toArray($monthly[0], $app->em);
            }

            $users_list[] = $usr;

            // $users_list[] = [
            // 'id' => $user->getId(),
            // 'name' => $user->getName(),
            // 'lastname' => $user->getLastname(),
            // 'number' => $user->getNumber(),
            // 'email' => $user->getEmail(),
            // 'identitycard' => $user->getIdentitycard(),
            // 'usertype' => [
            // "name" => $usertype->getName()
            // ],
            // ];
        }
    }


    $articles = $app->em->getRepository("Article")->createQueryBuilder('a')
        ->innerJoin("a.category", "c")
        ->leftJoin("c.parking", "p")
        ->where("p.id = :parking")
        ->andWhere("(
				a.name like :value or
				a.code like :value
			)")
        ->setParameter("parking", $parking)
        ->setParameter("value", '%' . $value . '%')
        ->getQuery()
        ->getResult();

    

    foreach ($articles as $article) {
        $rate = $article->getRate();

        $articles_list[] = [
            'id' => $article->getId(),
            'name' => $article->getName(),
            'description' => $article->getDescription(),
            'stock' => $article->getStock(),
            'code' => $article->getCode(),
            'rate' => [
                'cost' => $rate->getCost()
            ],
        ];
    }


    return new Response("Ok", [
        "Stay" => $stays_list,
        "User" => $users_list,
        "Article" => $articles_list,
    ]);
});

// Este parametro se usa para pruebas
$app->action("GET", "find_testing", function ($parking, $value) use ($app) {
    
    $stays_list = [];
    $users_list = [];
    $articles_list = [];

    $valueAlpa = strtoupper($value);

    if(strlen($value) == 14){ //CODIGO DE BARRAS
        $stays = $app->em->getRepository("Stay")->createQueryBuilder('s')
        ->innerJoin("s.parking", "p")
        ->where("p.id = :parking")
        ->andWhere("s.DateLeave is null")
        ->andWhere("s.rate is not null")
        ->andWhere("s.barcode  =:value")
        ->setParameter("parking", $parking)
        ->setParameter("value", $value)
        ->setMaxResults(10)
        ->getQuery()
        ->getResult();
        
        foreach($stays as $stay) {
        $user = $stay->getUser();
        $rate = $stay->getUser();
        $vehicle = $stay->getVehicle();
        $parking = $stay->getParking();
        
        $s = toArrayComplejo($stay, $app->em);
        
        $s['discounts'] = [];
        foreach($stay->getDiscounts() as $discount) {
            $o = toArray($discount, $app->em);
            $o['name'] = $discount->getAgreement()->getName();
            
            $s['discounts'][] = $o;
        }
        
        $s['vehicle'] = $vehicle ? $vehicle->getPlate() : "";
        $s['parking'] = $parking->getName();
        $stays_list[] = $s;
        }
        
        return new Response("Ok", ["Stay" => $stays_list,"User" => $users_list,"Article" => $articles_list,]);
        
        
    }
    elseif(substr($valueAlpa, 0, 2) === 'NC'){ //ALFANUMERICO
        $alpha = substr($valueAlpa, -3);
        $stays = $app->em->getRepository("Stay")->createQueryBuilder('s')
            ->innerJoin("s.parking", "p")
            ->where("p.id =:parking")
            ->andWhere("s.DateLeave is null")
            ->andWhere("s.rate is not null")
            ->andWhere("s.alphanumericcode =:value")
            ->setParameter("parking", $parking)
            ->setParameter("value", $alpha)
            ->orderBy("s.DateJoin","DESC")
            ->setMaxResults(1)
            ->getQuery()
            ->getResult();
            
            foreach($stays as $stay) {
            $user = $stay->getUser();
            $rate = $stay->getUser();
            $vehicle = $stay->getVehicle();
            $parking = $stay->getParking();
            
            $s = toArrayComplejo($stay, $app->em);
            
            $s['discounts'] = [];
            foreach($stay->getDiscounts() as $discount) {
                $o = toArray($discount, $app->em);
                $o['name'] = $discount->getAgreement()->getName();
                
                $s['discounts'][] = $o;
            }
            
            $s['vehicle'] = $vehicle ? $vehicle->getPlate() : "";
            $s['parking'] = $parking->getName();
            $stays_list[] = $s;
            }
        
        return new Response("Ok", ["Stay" => $stays_list,"User" => $users_list,"Article" => $articles_list,]);
    }

    $alpha = '';
    $stays = $app->em->getRepository("Stay")->createQueryBuilder('s')
        ->innerJoin("s.parking", "p")
        ->innerJoin("s.vehicle", "v")
        ->where("p.id = :parking")
        ->andWhere("s.DateLeave is null")
        ->andWhere("s.rate is not null")
        ->andWhere("s.vehicle is not null and v.plate =:value")
        ->setParameter("parking", $parking)
        ->setParameter("value", $value)
        ->setMaxResults(10)
        ->getQuery()
        ->getResult();
		
        foreach($stays as $stay) {
            $user = $stay->getUser();
            $rate = $stay->getUser();
            $vehicle = $stay->getVehicle();
            $parking = $stay->getParking();
            
            $s = toArrayComplejo($stay, $app->em);
            
            $s['discounts'] = [];
            foreach($stay->getDiscounts() as $discount) {
                $o = toArray($discount, $app->em);
                $o['name'] = $discount->getAgreement()->getName();
                
                $s['discounts'][] = $o;
            }
            
            $s['vehicle'] = $vehicle ? $vehicle->getPlate() : "";
            $s['parking'] = $parking->getName();
            $stays_list[] = $s;
        }

    if($stays){
        return new Response("Ok", ["Stay" => $stays_list,"User" => $users_list,"Article" => $articles_list,]);
    }

    $users = $app->em->getRepository("User")->createQueryBuilder('u')
        ->innerJoin("u.usertype", "ut")
        ->innerJoin("ut.parkings", "p")
        ->where("p.id = :parking")
        ->andWhere("u.active = 1")
        ->andWhere("u.enabled = 1")
        ->andWhere("u.employee = 0")
        ->andWhere("(
				u.name like :value or
				u.lastname like :value or
				u.identitycard like :value or
			    u.number like :value)
			")
        ->setParameter("parking", $parking)
        ->setParameter("value", '%' . $value . '%')
        ->getQuery()
        ->getResult();

    

    foreach ($users as $user) {
        $rate = $app->em->getRepository("RateStay")
            ->findOneBy(["id" => $user->getUsertype()->getRate()->getId()]);

        if (!$rate) {
            $usertype = $user->getUsertype();

            $usr = toArrayComplejo($user, $app->em);

            $monthly = $app->em->getRepository('Monthly')->createQueryBuilder('m')
                ->where("m.user = :user")
                ->andWhere("m.active = 1")
                ->andWhere("m.paid = 1")
                ->setParameter('user', $user->getId())
                ->orderBy("m.endDate", "desc")
                ->getQuery()
                ->setMaxResults(1)
                ->getResult();

            if (count($monthly) >= 1) {
                $usr['monthly'] = toArray($monthly[0], $app->em);
            }

            $users_list[] = $usr;

            // $users_list[] = [
            // 'id' => $user->getId(),
            // 'name' => $user->getName(),
            // 'lastname' => $user->getLastname(),
            // 'number' => $user->getNumber(),
            // 'email' => $user->getEmail(),
            // 'identitycard' => $user->getIdentitycard(),
            // 'usertype' => [
            // "name" => $usertype->getName()
            // ],
            // ];
        }
    }


    $articles = $app->em->getRepository("Article")->createQueryBuilder('a')
        ->innerJoin("a.category", "c")
        ->leftJoin("c.parking", "p")
        ->where("p.id = :parking")
        ->andWhere("(
				a.name like :value or
				a.code like :value
			)")
        ->setParameter("parking", $parking)
        ->setParameter("value", '%' . $value . '%')
        ->getQuery()
        ->getResult();

    

    foreach ($articles as $article) {
        $rate = $article->getRate();

        $articles_list[] = [
            'id' => $article->getId(),
            'name' => $article->getName(),
            'description' => $article->getDescription(),
            'stock' => $article->getStock(),
            'code' => $article->getCode(),
            'rate' => [
                'cost' => $rate->getCost()
            ],
        ];
    }


    return new Response("Ok", [
        "Stay" => $stays_list,
        "User" => $users_list,
        "Article" => $articles_list,
    ]);
});

$app->action("GET", "closeStay", function ($value) use ($app) {
//    $CONNECTION_DB = [
//        'driver' => 'pdo_mysql',
//        'host' => 'mysql-iparkings',
//        'user' => 'root',
//        'password' => 'dev',
//        'dbname' => 'nuevocentrodev',
//        'port' => 3307,
//    ];

    $CONNECTION_DB = [
        'driver' => 'pdo_mysql',
        'host' => 'localhost',
        'user' => 'root',
        'password' => 'adnoh.1',
        'dbname' => 'trescruces',
        'port' => 3306,
    ];

    $conn = mysqli_connect($CONNECTION_DB["host"], $CONNECTION_DB["user"], $CONNECTION_DB["password"], $CONNECTION_DB["dbname"], $CONNECTION_DB["port"]);

    if (!$conn) {
        return new Response("ERROR", mysqli_connect_error());
    }

    $query = "update stay s set s.DateLeave = now() where s.id = " . $value . ";";
    $result = mysqli_query($conn, $query);

    if (!$result) {
        mysqli_close($conn);
        return new Response("ERROR", "No se pudo actualizar");
    }

    $query = "insert into maronas_user (stayId) values(" . $value . ")";

    if (!mysqli_query($conn, $query)) {
        mysqli_close($conn);
        return new Response("ERROR", "No se pudo insertar en Maronas");
    }

    mysqli_close($conn);

    return new Response("Ok", 'Estadia Actualizada');
});
?>