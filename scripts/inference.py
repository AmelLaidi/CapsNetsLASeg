import argparse
from sklearn.metrics import precision_recall_fscore_support
from capsnets_laseg.inference.local_eval import pred_data_2D_per_sample, evaluate_2D
import json
from training_utils import get_model

def add_bool_arg(parser, name, default=False):
    """
    From: https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse
    Handles boolean cases from command line through the creating two mutually exclusive arguments: --name and --no-name.
    Args:
        parser (arg.parse.ArgumentParser): the parser you want to add the arguments to
        name: name of the common feature name for the two mutually exclusive arguments; dest = name
        default: default boolean for command line
    Returns:
        None
    """
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--" + name, dest=name, action="store_true")
    group.add_argument("--no-" + name, dest=name, action="store_false")
    parser.set_defaults(**{name:default})

if __name__ == "__main__":
    # parsing the arguments from the command prompt
    parser = argparse.ArgumentParser(description="For predicting and evaluating on Task 2 of the Medical Segmentation Decathlon using Capsule Networks and CNNs")
    parser.add_argument("--weights_path", type = str, required = True,
                        help = "Path to the saved weights.")
    parser.add_argument("--raw_dset_path", type = str, required = True,
                        help = "Path to the base directory where the unpreprocessed imagesTr and labelsTr directory are.")
    parser.add_argument("--model_name", type = str, required = True,
                        help = "Path to the base directory where you want to download and extract the tar file")
    parser.add_argument("--fold_json_path", type = str, required = True,
                        help = "Path to the json with the filenames split. If this is not specified, the json will be created in 'weights_dir.'")
    add_bool_arg(parser, "decoder", default = False) # defaults to extract = True
    parser.add_argument("--batch_size", type = int, required = False, default = 2,
                        help = "Batch size for the CNN should be 17 and for the Capsule Network, it should be 2.")
    parser.add_argument("--save_dir", type = str, required = False, default = "",
                        help = "Path to where you want to save the predictions (Defaults to not saving.)")
    args = parser.parse_args()

    input_shape = (256, 320, 1)
    local_train_path, local_label_path = os.path.join(args.raw_dset_path, "imagesTr"), os.path.join(args.raw_dset_path, "labelsTr")

    # loading the json
    with open(args.fold_json_path, "r") as fp:
        id_dict = json.load(fp)
    train_model, eval_model = get_model(args.model_name, None, decoder = args.decoder, inference = True)
    if eval_model is None: # dealing with the CNNs who only return train_model
        eval_model = train_model
    eval_model.load_weights(args.weights_path)
    # prediction
    print("Predicting", str(len(id_dict["test"])), "files")
    actual_y, pred, recon, orig_images = pred_data_2D_per_sample(eval_model, local_train_path, local_label_path, id_dict["test"], pad_shape = input_shape[:-1],\
                                            batch_size = args.batch_size)
    print("Groundtruth Shape: ", actual_y.shape, "\nPrediction Shape: ", pred.shape)
    # evaluation
    results = evaluate_2D(actual_y, pred)
    # Saving the predictions
    if args.save_dir != "":
        import numpy as np
        import os
        print("Saving the predictions in: ", args.save_dir)
        np.save(os.path.join(args.save_dir, "pred_seg.npy"), pred)
        if recon is not None:
            np.save(os.path.join(args.save_dir, "recon_seg.npy"), recon)
