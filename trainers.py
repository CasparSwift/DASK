import torch 
from utils.utils import AverageMeter
from evaluate import accuracy
import time

trainer_factory = {'graph_causal': graph_causal_Trainer,
                'graph': None,
                'causal': None}

class causal_Trainer(obj):
    def __init__(self, args, train_loader, model, loss_criterion, optimizers, total_steps, logger):
        self.args = args
        self.train_loader = train_loader
        self.model = model
        self.loss_criterion = loss_criterion
        self.optimizers = optimizers
        self.total_steps = total_steps
        self.logger = logger
        self.global_steps = 0

    def train_one_epoch(self):
        args = self.args
        train_loader = self.train_loader
        model = self.model
        loss_criterion = self.loss_criterion
        optimizers = self.optimizers
        total_steps = self.total_steps
        logger = self.logger

        sentim_loss_meter = AverageMeter()
        sentim_acc_meter = AverageMeter()
        time_meter = AverageMeter()
        env_enable_sentim_loss_meter = AverageMeter()
        env_enable_sentim_acc_meter = AverageMeter()

        ext_opt = optimizers[0]
        sentim_opt = optimizers[1]
        env_enable_sentim_opt = optimizers[2]

        model.train()
        for i, batch_data in enumerate(train_loader):
            self.global_steps += 1
            tokens, masks, positions, vms, augs, labels = batch_data
            start_time = time.time()

            sentim_probs, env_enable_sentim_probs, rationale_mask = model(tokens, masks, positions, vms, augs)

            extractor_loss, sentim_loss, env_enable_sentim_loss = loss_criterion(sentim_probs, \
                    env_enable_sentim_probs, labels, rationale_mask, masks)

            sentim_acc = accuracy(sentim_probs, labels)
            env_enable_sentim_acc = accuracy(env_enable_sentim_probs, labels)

            path = self.global_steps % 7
            if path in [0,1,2]:
                ext_opt.zero_grad()
                extractor_loss.backward()
                ext_opt.step()
            elif path in [3,4]:
                sentim_opt.zero_grad()
                sentim_loss.backward()
                sentim_opt.step()
            else:
                env_enable_sentim_opt.zero_grad()
                env_enable_sentim_loss.backward()
                env_enable_sentim_opt.step()

            end_time = time.time()
            time_meter.update(start_time-end_time)
            sentim_loss_meter.update(sentim_loss)
            sentim_acc_meter.update(sentim_acc)
            env_enable_sentim_acc_meter.update(env_enable_sentim_acc)
            env_enable_sentim_loss_meter.update(env_enable_sentim_loss)

            if global_steps % self.args.print_freq==0:
                log_string = 'Iteration[{0}]\t' \
                    'time: {batch_time.val:.3f}({batch_time.avg:.3f})\t' \
                    'sentiment_loss: {sentim_loss.val:.3f}({sentim_loss.avg:.3f})\t' \
                    'env_enable_sentiment_loss: {env_enable_sentim_loss.val:.3f}({env_enable_sentim_loss.avg:.3f})' \

                    'sentiment_accuracy: {sentim_acc.val:.3f}({sentim_acc.avg:.3f})' \
                    'env_enable_sentiment_acc: {env_enable_sentim_acc.val:.3f}({env_enable_sentim_acc.avg:.3f})'.format(
                        i, batch_time=time_meter, env_enable_sentim_loss=env_enable_sentim_loss,
                        sentim_loss=sentim_loss_meter, env_enable_sentim_acc=env_enable_sentim_acc,
                        sentim_acc=sentim_acc_meter)

                logger.info(log_string)

        return self.global_steps




class graph_causal_Trainer(obj):
    # not complete
    def __init__(self, args, train_loader, model, loss_criterion, optimizers, total_steps, logger):
        self.args = args
        self.train_loader = train_loader
        self.model = model
        self.loss_criterion = loss_criterion
        self.optimizers = optimizers
        self.total_steps = total_steps
        self.logger = logger
        self.global_steps = 0

    def train_one_epoch(self):
        '''
        main train procedure
        '''
        args = self.args
        train_loader = self.train_loader
        model = self.model
        loss_criterion = self.loss_criterion
        optimizers = self.optimizers
        total_steps = self.total_steps
        logger = self.logger

        dom_loss_meter = AverageMeter()
        sentim_loss_meter = AverageMeter()
        dom_loss_u_meter = AverageMeter()
        dom_acc_meter = AverageMeter()
        dom_acc_u_meter = AverageMeter()
        sentim_acc_meter = AverageMeter()
        time_meter = AverageMeter()
        ext_opt = optimizers[2]
        dom_opt = optimizers[1]
        sentim_opt = optimizers[0]
        model.train()
        # lamda = 2/(1+math.exp(-10*global_steps/total_steps))-1

        for i, labeled_batch, unlabeled_batch in enumerate(train_loader):
            self.global_steps += 1 
            lamda = 2/(1+math.exp(-10*global_steps/total_steps))-1
            path = global_steps % 7
            tokens, masks, positions, vms, labels, domains, _ = labeled_batch
            start_time = time.time()

            # outputs = 
            sentim, env_sentim, dom = model(tokens, masks, positions, vms)
            ext_loss, dom_loss, sentim_loss, env_enable_loss = loss_criterion(sentim, labels)
            sentim_env_loss = loss_criterion(sentim)
            dom_loss = loss_criterion(dom, domains)

            sentim_acc = accuracy(sentim, labels)
            dom_acc = accuracy(dom, domains)

            # optimizer_wrapper.step(global_steps, )
            if path in [0,1,2,3,4]:
                ext_opt.zero_grad()
                dom_loss_u.backward()
                ext_opt.step()
            elif path in [5,6]:
                dom_opt.zero_grad()
                dom_loss_u.backward()
                dom_opt.step()
            

            tokens_u, masks_u, positions_u, vms_u, domains_u, _ = unlabeled_batch
            sentim_u, dom_u = model(tokens_u, masks_u, positions_u, vms_u)
            dom_loss_u = loss_criterion(dom_u, domains_u)
            dom_acc_u = accuracy(dom_u, domains_u)

            dom_loss_meter.update(dom_loss)
            dom_loss_u_meter.update(dom_loss_u)
            sentim_loss_meter.update(sentim_loss)
            dom_acc_meter.update(dom_acc)
            dom_acc_u_meter.update(dom_acc_u)
            sentim_acc_meter.update(sentim_acc)
        
            if path in [0,1,2,3,4]:
                ext_opt.zero_grad()
                dom_loss_u.backward()
                ext_opt.step()
            elif path in [5,6]:
                dom_opt.zero_grad()
                dom_loss_u.backward()
                dom_opt.step()
            end_time = time.time()
            time_meter.update(end_time - start_time)

            if i % args.print_freq==0:
                log_string = 'Iteration[{0}]\t' \
                    'time {batch_time.val:.3f}({batch_time.avg:.3f})\t' \
                    'domain_loss {dom_loss.val:.3f}({dom_loss.avg:.3f})\t' \
                    'unlabeled_domain_loss {dom_loss_u.val:.3f}({dom_loss_u.avg:.3f})\t' \
                    'sentiment_loss {sentim_loss.val:.3f}({sentim_loss.avg:.3f})\t' \
                    'domain_accuracy {dom_acc.val:.3f}({dom_acc.avg:.3f})\t' \
                    'unlabeled_domain_accuracy {dom_acc_u.val:.3f}({dom_acc_u.avg:.3f})\t' \
                    'sentiment_accuracy {sentim_acc.val:.3f}({sentim_acc.avg:.3f})'.format(
                        i, batch_time=time_meter, dom_loss=dom_loss_meter, dom_loss_u=dom_loss_u_meter,
                        sentim_loss=sentim_loss_meter, dom_acc=dom_acc_meter, dom_acc_u=dom_acc_u_meter,
                        sentim_acc=sentim_acc_meter)

                logger.info(log_string)


        return self.global_steps

def DA_train_one_epoch(args, train_loader, model, loss_criterion, optimizer, global_steps, total_steps, logger):
    '''
    main train procedure
    '''
    dom_loss_meter = AverageMeter()
    sentim_loss_meter = AverageMeter()
    dom_loss_u_meter = AverageMeter()
    dom_acc_meter = AverageMeter()
    dom_acc_u_meter = AverageMeter()
    sentim_acc_meter = AverageMeter()
    time_meter = AverageMeter()
    ext_opt = optimizers[2]
    dom_opt = optimizers[1]
    sentim_opt = optimizers[0]
    model.train()
    # lamda = 2/(1+math.exp(-10*global_steps/total_steps))-1

    for i, labeled_batch, unlabeled_batch in enumerate(train_loader):
        global_steps += 1 
        lamda = 2/(1+math.exp(-10*global_steps/total_steps))-1
        path = global_steps % 7
        tokens, masks, positions, vms, labels, domains, _ = labeled_batch
        start_time = time.time()
        sentim, dom = model(tokens, masks, positions, vms)
        sentim_loss = loss_criterion(sentim, labels)
        dom_loss = loss_criterion(dom, domains)

        sentim_acc = accuracy(sentim, labels)
        dom_acc = accuracy(dom, domains)

        if path in [0,1,2,3,4]:
            ext_opt.zero_grad()
            sentim_loss.backward()
            dom_loss.backward()
            ext_opt.step()
        elif path==5:
            dom_opt.zero_grad()
            dom_loss.backward()
            dom_opt.step()
        elif path==6:
            sentim_opt.zero_grad()
            sentim_loss.backward()
            sentim_opt.step()
        

        tokens_u, masks_u, positions_u, vms_u, domains_u, _ = unlabeled_batch
        sentim_u, dom_u = model(tokens_u, masks_u, positions_u, vms_u)
        dom_loss_u = loss_criterion(dom_u, domains_u)
        dom_acc_u = accuracy(dom_u, domains_u)

        dom_loss_meter.update(dom_loss)
        dom_loss_u_meter.update(dom_loss_u)
        sentim_loss_meter.update(sentim_loss)
        dom_acc_meter.update(dom_acc)
        dom_acc_u_meter.update(dom_acc_u)
        sentim_acc_meter.update(sentim_acc)
    
        if path in [0,1,2,3,4]:
            ext_opt.zero_grad()
            dom_loss_u.backward()
            ext_opt.step()
        elif path in [5,6]:
            dom_opt.zero_grad()
            dom_loss_u.backward()
            dom_opt.step()
        end_time = time.time()
        time_meter.update(end_time - start_time)

        if i % args.print_freq==0:
            log_string = 'Iteration[{0}]\t' \
                'time {batch_time.val:.3f}({batch_time.avg:.3f})\t' \
                'domain_loss {dom_loss.val:.3f}({dom_loss.avg:.3f})\t' \
                'unlabeled_domain_loss {dom_loss_u.val:.3f}({dom_loss_u.avg:.3f})\t' \
                'sentiment_loss {sentim_loss.val:.3f}({sentim_loss.avg:.3f})\t' \
                'domain_accuracy {dom_acc.val:.3f}({dom_acc.avg:.3f})\t' \
                'unlabeled_domain_accuracy {dom_acc_u.val:.3f}({dom_acc_u.avg:.3f})\t' \
                'sentiment_accuracy {sentim_acc.val:.3f}({sentim_acc.avg:.3f})'.format(
                    i, batch_time=time_meter, dom_loss=dom_loss_meter, dom_loss_u=dom_loss_u_meter,
                    sentim_loss=sentim_loss_meter, dom_acc=dom_acc_meter, dom_acc_u=dom_acc_u_meter,
                    sentim_acc=sentim_acc_meter)

            logger.info(log_string)


        return global_steps